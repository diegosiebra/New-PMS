#!/usr/bin/env python3
"""
LangGraph Agent Service Runner
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Validate required environment variables
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY", 
        "DATABASE_URL",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these variables in your .env file or environment")
        sys.exit(1)
    
    # Get configuration
    port = int(os.getenv("PORT", 3001))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("LANGGRAPH_DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting LangGraph Agent Service")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"🤖 Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )

if __name__ == "__main__":
    main()
