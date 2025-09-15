"""
RAG Service for Document Retrieval
Uses LangChain components and OpenAI embeddings for intelligent document search
"""

import os
import logging
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from database import db_service

logger = logging.getLogger(__name__)

class SupabaseRAGRetriever(BaseRetriever):
    """Custom retriever that uses Supabase match_documents3 function with scope filtering"""
    
    def __init__(self, scope_tags: List[str] = None, limit: int = 5, match_threshold: float = 0.7):
        super().__init__()
        self._scope_tags = scope_tags or ["GLOBAL"]
        self._limit = limit
        self._match_threshold = match_threshold
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve relevant documents using Supabase RAG"""
        try:
            # Use database service to search documents (sync version)
            import asyncio
            documents_data = asyncio.run(db_service.search_documents_rag(
                query, 
                self._scope_tags, 
                self._limit
            ))
            
            # Convert to LangChain Document format
            documents = []
            for doc_data in documents_data:
                content = doc_data.get("content", "")
                metadata = doc_data.get("metadata", {})
                
                # Add document ID and scope to metadata
                metadata.update({
                    "id": doc_data.get("id"),
                    "scope": metadata.get("scope", "GLOBAL"),
                    "source": "supabase_documents"
                })
                
                documents.append(Document(page_content=content, metadata=metadata))
            
            logger.info(f"Retrieved {len(documents)} documents for query: '{query}'")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    async def aget_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Async version of document retrieval"""
        try:
            # Use database service to search documents
            documents_data = await db_service.search_documents_rag(
                query, 
                self._scope_tags, 
                self._limit
            )
            
            # Convert to LangChain Document format
            documents = []
            for doc_data in documents_data:
                content = doc_data.get("content", "")
                metadata = doc_data.get("metadata", {})
                
                # Add document ID and scope to metadata
                metadata.update({
                    "id": doc_data.get("id"),
                    "scope": metadata.get("scope", "GLOBAL"),
                    "source": "supabase_documents"
                })
                
                documents.append(Document(page_content=content, metadata=metadata))
            
            logger.info(f"Retrieved {len(documents)} documents for query: '{query}'")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

class RAGService:
    """Service for handling RAG operations with reservation context"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    def extract_scope_tags_from_reservation(self, reservation: Dict[str, Any]) -> List[str]:
        """Extract scope tags from reservation for RAG search"""
        scope_tags = ["GLOBAL"]  # Default scope
        
        if reservation:
            reservation_tags = reservation.get("tags", {})
            
            # Extract relevant tags for scope
            if isinstance(reservation_tags, dict):
                # Extract building and apartment codes
                building_code = reservation_tags.get("buildingCode")
                apartment_code = reservation_tags.get("apartmentCode")
                
                if building_code:
                    scope_tags.append(building_code)
                if apartment_code:
                    scope_tags.append(apartment_code)
                
                # Add any other relevant tags
                for key, value in reservation_tags.items():
                    if key not in ["buildingCode", "apartmentCode"] and isinstance(value, str):
                        scope_tags.append(value)
        
        # Remove duplicates and ensure we have at least GLOBAL
        return list(set(scope_tags))
    
    def create_retriever(self, scope_tags: List[str] = None, limit: int = 5) -> SupabaseRAGRetriever:
        """Create a retriever with specific scope tags"""
        return SupabaseRAGRetriever(scope_tags=scope_tags, limit=limit)
    
    async def search_documents(self, query: str, reservation: Dict[str, Any] = None, limit: int = 5) -> List[Document]:
        """Search documents with reservation context"""
        try:
            # Extract scope tags from reservation
            scope_tags = ["GLOBAL"]
            if reservation:
                scope_tags = self.extract_scope_tags_from_reservation(reservation)
            
            # Create retriever
            retriever = self.create_retriever(scope_tags, limit)
            
            # Retrieve documents
            documents = await retriever.ainvoke(query)
            
            logger.info(f"RAG search for '{query}' with scopes {scope_tags}: {len(documents)} results")
            return documents
            
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return []
    
    def format_documents_for_response(self, documents: List[Document], query: str) -> str:
        """Format retrieved documents for agent response"""
        if not documents:
            return f"ℹ️ Nenhuma informação encontrada sobre '{query}' na base de conhecimento."
        
        results = []
        for i, doc in enumerate(documents, 1):
            content = doc.page_content
            metadata = doc.metadata
            scope = metadata.get("scope", "GLOBAL")
            
            # Return full content without truncation
            # Add scope information if not global
            scope_info = f" (Escopo: {scope})" if scope != "GLOBAL" else ""
            results.append(f"{i}. {content}{scope_info}")
        
        return f"📚 Informações encontradas sobre '{query}':\n\n" + "\n\n".join(results)

# Global RAG service instance
rag_service = RAGService()
