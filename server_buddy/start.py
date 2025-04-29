#!/usr/bin/env python3
"""
Production startup script for Buddy Server
"""
import os
import sys
import uvicorn
from main import app

def main():
    """Main entry point for production deployment"""
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    
    # Check if required environment variables are set
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable is required")
        sys.exit(1)
    
    print(f"Starting Buddy Server on {host}:{port}")
    print(f"Environment: {'Production' if os.getenv('PORT') else 'Development'}")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
