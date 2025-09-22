"""
Checkpoint Manager - Gerenciador de Checkpoints para LangGraph
Centraliza toda a configuração e criação de checkpoints para memória persistente
Suporta PostgresSaver (Supabase) e InMemorySaver como fallback
"""

import os
import logging
from typing import Optional, Union
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

logger = logging.getLogger(__name__)

class CheckpointManager:
    """Gerenciador centralizado de checkpoints para LangGraph"""
    
    def __init__(self, 
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None,
                 fallback_to_memory: bool = True):
        """
        Inicializa o CheckpointManager
        
        Args:
            supabase_url: URL do Supabase (se None, usa SUPABASE_URL do env)
            supabase_key: Chave do Supabase (se None, usa SUPABASE_SERVICE_KEY do env)
            fallback_to_memory: Se True, usa InMemorySaver como fallback
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        self.fallback_to_memory = fallback_to_memory
        
        # Cache do checkpoint para evitar recriação
        self._checkpointer: Optional[BaseCheckpointSaver] = None
        
        logger.info(f"CheckpointManager initialized with Supabase URL: {self.supabase_url[:20]}..." if self.supabase_url else "No Supabase URL")
    
    def get_checkpointer(self) -> BaseCheckpointSaver:
        """
        Obtém o checkpointer configurado
        
        Returns:
            BaseCheckpointSaver: Instância do checkpointer (PostgresSaver ou InMemorySaver)
        """
        if self._checkpointer is not None:
            return self._checkpointer
        
        self._checkpointer = self._create_checkpointer()
        return self._checkpointer
    
    def _create_checkpointer(self) -> BaseCheckpointSaver:
        """
        Cria o checkpointer apropriado baseado na configuração
        
        Returns:
            BaseCheckpointSaver: Instância do checkpointer
        """
        # Tentar criar PostgresSaver primeiro
        if self.supabase_url and self.supabase_key:
            try:
                postgres_checkpointer = self._create_postgres_checkpointer()
                logger.info("✅ PostgresSaver checkpointer created successfully")
                return postgres_checkpointer
                
            except Exception as e:
                logger.warning(f"❌ Failed to create PostgresSaver: {e}")
                if not self.fallback_to_memory:
                    raise e
        
        # Fallback para InMemorySaver
        if self.fallback_to_memory:
            logger.info("🔄 Falling back to InMemorySaver")
            return InMemorySaver()
        
        raise ValueError("No valid checkpointer configuration found")
    
    def _create_postgres_checkpointer(self) -> PostgresSaver:
        """
        Cria um PostgresSaver usando as credenciais do Supabase
        
        Returns:
            PostgresSaver: Instância do PostgresSaver
            
        Raises:
            ValueError: Se as credenciais não estiverem disponíveis
            Exception: Se houver erro na conexão
        """
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        # Converter URL do Supabase para string de conexão PostgreSQL
        db_url = self._build_postgres_url()
        
        logger.info(f"Creating PostgresSaver with URL: {db_url[:50]}...")
        
        # Criar PostgresSaver usando pool de conexões psycopg2
        try:
            import psycopg2
            from psycopg2 import pool
            
            # Criar pool de conexões
            connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=db_url
            )
            
            # Criar PostgresSaver com pool de conexões
            checkpointer = PostgresSaver(connection_pool)
            
            logger.info("PostgresSaver created successfully with connection pool")
            return checkpointer
            
        except ImportError:
            logger.error("psycopg2 not available, falling back to InMemorySaver")
            from langgraph.checkpoint.memory import InMemorySaver
            return InMemorySaver()
            
        except Exception as e:
            logger.error(f"Failed to create PostgresSaver: {e}")
            # Fallback para InMemorySaver
            logger.warning("Falling back to InMemorySaver due to error")
            from langgraph.checkpoint.memory import InMemorySaver
            return InMemorySaver()
    
    def _build_postgres_url(self) -> str:
        """
        Constrói a URL de conexão PostgreSQL a partir da URL do Supabase
        
        Suporta tanto Supabase Cloud quanto self-hosted
        
        Returns:
            str: URL de conexão PostgreSQL
        """
        if not self.supabase_url.startswith("https://"):
            raise ValueError(f"Invalid Supabase URL format: {self.supabase_url}")
        
        # Remover https:// da URL
        host_part = self.supabase_url.replace("https://", "")
        
        # Para Supabase Cloud: project.supabase.co -> db.project.supabase.co:5432/postgres
        # Para Supabase self-hosted: supabase.ia2n.com.br -> supabase.ia2n.com.br:5432/postgres
        if host_part.endswith(".supabase.co"):
            # Supabase Cloud
            db_host = host_part.replace(".supabase.co", ".supabase.co")
            db_host = db_host.replace("https://", "").replace("https://", "")
            db_url = f"postgresql://postgres:{self.supabase_key}@{db_host}:5432/postgres"
        else:
            # Supabase self-hosted (como supabase.ia2n.com.br)
            db_url = f"postgresql://postgres:{self.supabase_key}@{host_part}:5432/postgres"
        
        # Adicionar parâmetros SSL
        db_url += "?sslmode=require"
        
        logger.info(f"Built PostgreSQL URL for self-hosted Supabase: {db_url[:50]}...")
        return db_url
    
    
    def get_connection_info(self) -> dict:
        """
        Retorna informações sobre a configuração atual
        
        Returns:
            dict: Informações da configuração
        """
        return {
            "supabase_url": self.supabase_url[:20] + "..." if self.supabase_url else None,
            "supabase_key_configured": bool(self.supabase_key),
            "fallback_to_memory": self.fallback_to_memory,
            "checkpointer_type": type(self._checkpointer).__name__ if self._checkpointer else "Not created",
            "postgres_url": self._build_postgres_url()[:50] + "..." if self.supabase_url and self.supabase_key else None
        }
    
    def reset_checkpointer(self) -> None:
        """
        Reseta o checkpointer (força recriação)
        """
        self._checkpointer = None
        logger.info("Checkpointer reset - will be recreated on next access")
    
    @classmethod
    def create_from_env(cls, fallback_to_memory: bool = True) -> 'CheckpointManager':
        """
        Cria CheckpointManager usando variáveis de ambiente
        
        Args:
            fallback_to_memory: Se True, usa InMemorySaver como fallback
            
        Returns:
            CheckpointManager: Instância configurada
        """
        return cls(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_KEY"),
            fallback_to_memory=fallback_to_memory
        )

# Instância global para reutilização
checkpoint_manager = CheckpointManager.create_from_env()
