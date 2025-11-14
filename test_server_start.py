#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from claude_code_server_api import create_app, load_config
    print("✓ Imports successful")
    
    config = load_config("config.yaml")
    print(f"✓ Config loaded: {config.working_directory}")
    
    app = create_app(config)
    print("✓ App created successfully")
    print("\nReady to start server!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
