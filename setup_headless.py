#!/usr/bin/env python3
"""
Helper script to configure browser-use for headless operation.
"""

import os
import sys

def setup_headless_environment():
    """Set up environment variables for headless browser operation."""
    
    # Set environment variables for headless operation
    os.environ['BROWSER_USE_HEADLESS'] = 'true'
    os.environ['PLAYWRIGHT_HEADLESS'] = 'true'
    
    # Additional browser configuration
    os.environ['BROWSER_USE_VIEWPORT_WIDTH'] = '1920'
    os.environ['BROWSER_USE_VIEWPORT_HEIGHT'] = '1080'
    
    # Disable images and other resources for faster loading
    os.environ['BROWSER_USE_DISABLE_IMAGES'] = 'true'
    os.environ['BROWSER_USE_DISABLE_CSS'] = 'false'  # Keep CSS for proper layout
    os.environ['BROWSER_USE_DISABLE_JS'] = 'false'   # Keep JS for functionality
    
    print("🔧 Headless environment configured:")
    print("   - Headless mode: enabled")
    print("   - Viewport: 1920x1080")
    print("   - Images: disabled (for speed)")
    print("   - CSS: enabled")
    print("   - JavaScript: enabled")

if __name__ == "__main__":
    setup_headless_environment() 