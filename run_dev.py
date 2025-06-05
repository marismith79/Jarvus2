#!/usr/bin/env python
import os
from dotenv import load_dotenv
from jarvus_app.__main__ import create_app

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=True) 