"""
Configuração de Tracing para LangGraph
Permite visualizar automaticamente qual agente foi chamado, quais tools foram executados, etc.
"""

import os
from typing import Dict, Any

def setup_langsmith_tracing():
    """Configura LangSmith para tracing automático"""
    # Descomente e configure estas variáveis para usar LangSmith
    # os.environ["LANGCHAIN_TRACING_V2"] = "true"
    # os.environ["LANGCHAIN_API_KEY"] = "your_langsmith_api_key"
    # os.environ["LANGCHAIN_PROJECT"] = "reservaflow-agent-service"
    pass

def setup_console_tracing():
    """Configura tracing no console (sem LangSmith)"""
    # Ativa logs detalhados do LangGraph
    os.environ["LANGGRAPH_LOG_LEVEL"] = "debug"
    os.environ["LANGGRAPH_DEBUG"] = "true"

def get_tracing_config() -> Dict[str, Any]:
    """Retorna configuração de tracing baseada no ambiente"""
    return {
        "langsmith_enabled": os.getenv("LANGCHAIN_TRACING_V2") == "true",
        "console_tracing": os.getenv("LANGGRAPH_DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LANGGRAPH_LOG_LEVEL", "info")
    }
