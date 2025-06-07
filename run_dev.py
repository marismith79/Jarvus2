#!/usr/bin/env python
import os
from dotenv import load_dotenv
from pathlib import Path
from jarvus_app import create_app

# Clear any existing OpenAI environment variables
for key in list(os.environ.keys()):
    if 'OPENAI' in key:
        del os.environ[key]

# Get the project root directory
project_root = Path(__file__).parent
env_path = project_root / '.env'

# Load environment variables from .env file
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    print("Warning: .env file not found at", env_path)

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=True) 