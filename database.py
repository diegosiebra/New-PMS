import os
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant information from database"""
        try:
            response = self.supabase.table("tenantnew").select("*").eq("id", tenant_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {e}")
            return None
    
    async def get_tenant_by_instance(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """Get tenant information by Evolution API instance name"""
        try:
            # Search for tenant where settings.evolution.instanceName matches the instance
            response = self.supabase.table("tenantnew").select("*").execute()
            
            if response.data:
                for tenant in response.data:
                    settings = tenant.get("settings", {})
                    evolution_config = settings.get("evolution", {})
                    tenant_instance = evolution_config.get("instanceName")
                    
                    if tenant_instance == instance_name:
                        logger.info(f"Found tenant {tenant['id']} for instance {instance_name}")
                        return tenant
            
            logger.warning(f"No tenant found for instance {instance_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting tenant by instance {instance_name}: {e}")
            return None
    
    async def get_agent_configurations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get agent configurations for a tenant"""
        try:
            response = self.supabase.table("agent_configurations").select("*").eq("tenant_id", tenant_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting agent configurations for tenant {tenant_id}: {e}")
            return []
    
    async def update_agent_configuration(self, tenant_id: str, agent_name: str, configuration: Dict[str, Any]) -> bool:
        """Update agent configuration for a tenant"""
        try:
            response = self.supabase.table("agent_configurations").update({
                "configuration": configuration
            }).eq("tenant_id", tenant_id).eq("agent_name", agent_name).execute()
            
            if response.data:
                logger.info(f"Updated configuration for agent {agent_name} in tenant {tenant_id}")
                return True
            else:
                logger.warning(f"No agent {agent_name} found for tenant {tenant_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating agent configuration for tenant {tenant_id}, agent {agent_name}: {e}")
            return False
    
    async def update_agent_prompt(self, tenant_id: str, agent_name: str, prompt: str) -> bool:
        """Update agent prompt for a tenant"""
        try:
            response = self.supabase.table("agent_configurations").update({
                "prompt": prompt
            }).eq("tenant_id", tenant_id).eq("agent_name", agent_name).execute()
            
            if response.data:
                logger.info(f"Updated prompt for agent {agent_name} in tenant {tenant_id}")
                return True
            else:
                logger.warning(f"No agent {agent_name} found for tenant {tenant_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating agent prompt for tenant {tenant_id}, agent {agent_name}: {e}")
            return False
    
    async def log_agent_execution(self, execution: Dict[str, Any]) -> bool:
        """Log agent execution to database"""
        try:
            response = self.supabase.table("agent_executions").insert({
                "tenant_id": execution["tenant_id"],
                "conversation_id": execution["conversation_id"],
                "agent_type": execution["agent_type"],
                "agent_name": execution["agent_name"],
                "input": execution.get("input"),
                "output": execution.get("output"),
                "status": execution["status"],
                "execution_time": execution.get("execution_time"),
                "error_message": execution.get("error_message"),
                "created_at": execution.get("created_at")
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error logging agent execution: {e}")
            return False
    
    async def get_conversation_history(self, tenant_id: str, whatsapp_number: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for a WhatsApp number"""
        try:
            # Get conversation history from agent_executions table
            response = self.supabase.table("agent_executions").select("*").eq("tenant_id", tenant_id).eq("conversation_id", whatsapp_number).order("created_at", desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def get_reservations_by_whatsapp(self, tenant_id: str, whatsapp_number: str) -> List[Dict[str, Any]]:
        """Get reservations for a WhatsApp number by joining Customers and Reservations tables"""
        try:
            # Use Supabase join syntax with proper foreign key relationship
            response = self.supabase.table("Reservations").select("""
                id,
                created_at,
                reservationid,
                checkindate,
                checkintime,
                checkoutdate,
                checkouttime,
                listingid,
                clientid,
                guestsdetails,
                status,
                number_of_documents,
                payload,
                tags,
                docs_imediato,
                status_step_id,
                in_manual,
                tenant_id,
                Customers!inner(
                    customername,
                    customerwhatsapp,
                    externalid,
                    birthday,
                    fathersname,
                    mothersname,
                    cpf_rg_passaporte,
                    wasvalidated
                )
            """).eq("tenant_id", tenant_id).eq("Customers.customerwhatsapp", whatsapp_number).execute()
            
            logger.info(f"Found {len(response.data or [])} reservations for WhatsApp {whatsapp_number}")
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting reservations for WhatsApp {whatsapp_number}: {e}")
            # Fallback to manual join if the relationship isn't available yet
            logger.info("Falling back to manual join method...")
            return await self._get_reservations_manual_join(tenant_id, whatsapp_number)
    
    async def _get_reservations_manual_join(self, tenant_id: str, whatsapp_number: str) -> List[Dict[str, Any]]:
        """Fallback method for manual join when foreign key relationship isn't available"""
        try:
            # First, get the customer by WhatsApp number
            customer_response = self.supabase.table("Customers").select("*").eq("tenant_id", tenant_id).eq("customerwhatsapp", whatsapp_number).execute()
            
            if not customer_response.data:
                logger.info(f"No customer found for WhatsApp {whatsapp_number}")
                return []
            
            customer = customer_response.data[0]
            customer_external_id = customer.get("externalid")
            
            if not customer_external_id:
                logger.warning(f"Customer found but no external ID for WhatsApp {whatsapp_number}")
                return []
            
            # Then get reservations for this customer
            reservations_response = self.supabase.table("Reservations").select("*").eq("tenant_id", tenant_id).eq("clientid", customer_external_id).execute()
            
            # Combine customer data with each reservation
            reservations_with_customer = []
            for reservation in reservations_response.data or []:
                reservation["Customers"] = customer
                reservations_with_customer.append(reservation)
            
            logger.info(f"Found {len(reservations_with_customer)} reservations for customer {customer.get('customername')} (manual join)")
            return reservations_with_customer
            
        except Exception as e:
            logger.error(f"Error in manual join for WhatsApp {whatsapp_number}: {e}")
            return []
    
    async def get_reservation_by_id(self, tenant_id: str, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific reservation by ID with customer information"""
        try:
            # Use Supabase join syntax with proper foreign key relationship
            response = self.supabase.table("Reservations").select("""
                id,
                created_at,
                reservationid,
                checkindate,
                checkintime,
                checkoutdate,
                checkouttime,
                listingid,
                clientid,
                guestsdetails,
                status,
                number_of_documents,
                payload,
                tags,
                docs_imediato,
                status_step_id,
                in_manual,
                tenant_id,
                Customers!inner(
                    customername,
                    customerwhatsapp,
                    externalid,
                    birthday,
                    fathersname,
                    mothersname,
                    cpf_rg_passaporte,
                    wasvalidated
                )
            """).eq("tenant_id", tenant_id).eq("reservationid", reservation_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting reservation {reservation_id}: {e}")
            # Fallback to manual join if the relationship isn't available yet
            logger.info("Falling back to manual join method for reservation by ID...")
            return await self._get_reservation_by_id_manual_join(tenant_id, reservation_id)
    
    async def _get_reservation_by_id_manual_join(self, tenant_id: str, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Fallback method for manual join when foreign key relationship isn't available"""
        try:
            # First get the reservation
            reservation_response = self.supabase.table("Reservations").select("*").eq("tenant_id", tenant_id).eq("reservationid", reservation_id).execute()
            
            if not reservation_response.data:
                return None
            
            reservation = reservation_response.data[0]
            client_id = reservation.get("clientid")
            
            if client_id:
                # Get customer information
                customer_response = self.supabase.table("Customers").select("*").eq("tenant_id", tenant_id).eq("externalid", client_id).execute()
                
                if customer_response.data:
                    reservation["Customers"] = customer_response.data[0]
            
            return reservation
            
        except Exception as e:
            logger.error(f"Error in manual join for reservation {reservation_id}: {e}")
            return None
    
    async def search_documents_rag(self, query: str, scope_tags: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents using RAG with scope filtering using match_documents3 function"""
        try:
            # Add default scope if not provided
            if not scope_tags:
                scope_tags = ["GLOBAL"]
            else:
                scope_tags = scope_tags + ["GLOBAL"]  # Always include global scope
            
            # Remove duplicates
            scope_tags = list(set(scope_tags))
            
            # Use your existing match_documents3 function
            # First, we need to generate embeddings for the query
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            query_embedding = embeddings.embed_query(query)
            
            # Create filter with scope tags
            filter_data = {
                "scope": scope_tags
            }
            
            response = self.supabase.rpc('match_documents3', {
                'query_embedding': query_embedding,
                'match_count': limit,
                'filter': filter_data
            }).execute()
            
            logger.info(f"RAG search for '{query}' with scopes {scope_tags}: {len(response.data or [])} results")
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error searching documents with RAG: {e}")
            # Fallback to simple text search if vector search fails
            return await self._search_documents_fallback(query, scope_tags, limit)
    
    async def _search_documents_fallback(self, query: str, scope_tags: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback method for document search without vector similarity"""
        try:
            # Simple text search in content
            response = self.supabase.table("documents").select("*").ilike("content", f"%{query}%").limit(limit).execute()
            
            # Filter by scope in metadata if available
            filtered_results = []
            for doc in response.data or []:
                metadata = doc.get("metadata", {})
                doc_scope = metadata.get("scope", "GLOBAL")
                
                if doc_scope in (scope_tags or ["GLOBAL"]):
                    filtered_results.append(doc)
            
            logger.info(f"Fallback search for '{query}': {len(filtered_results)} results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error in fallback document search: {e}")
            return []
    
    async def save_conversation_message(self, tenant_id: str, whatsapp_number: str, message: str, from_me: bool) -> bool:
        """Save a conversation message to database"""
        try:
            # Log conversation as agent execution instead of using n8n_chat_histories
            agent_name = "User" if not from_me else "Bot"
            agent_type = "user_message" if not from_me else "bot_response"
            
            await self.log_agent_execution({
                "tenant_id": tenant_id,
                "conversation_id": whatsapp_number,
                "agent_type": agent_type,
                "agent_name": agent_name,
                "input": {"message": message},
                "output": None,
                "status": "success",
                "execution_time": None,
                "error_message": None,
                "created_at": "now()"
            })
            return True
        except Exception as e:
            logger.error(f"Error saving conversation message: {e}")
            return False

# Global database service instance
db_service = DatabaseService()
