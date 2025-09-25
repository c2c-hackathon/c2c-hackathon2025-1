#!/usr/bin/env python3
"""
Browser Launcher Script

Opens the C2C Hackathon documentation in the default web browser.
"""

import webbrowser
import sys

def open_documentation():
    """
    Open the C2C Hackathon documentation in the default browser.
    
    Returns:
        bool: True if successful, False otherwise
    """
    url = "https://c2c-hackathon.github.io/docs/index.html"
    
    try:
        print(f"Opening documentation at: {url}")
        webbrowser.open(url)
        print("Documentation opened successfully in your default browser!")
        return True
    except Exception as e:
        print(f"Error opening browser: {e}")
        return False

if __name__ == "__main__":
    """
    Main execution - opens the documentation URL in default browser.
    """
    success = open_documentation()
    
    if not success:
        print("\nAlternatively, you can manually open this URL in your browser:")
        print("https://c2c-hackathon.github.io/docs/index.html")
        sys.exit(1)