#!/usr/bin/env python3
"""
Entry point for the IFTTT Twitter Webhook application.
"""

import sys
import os

# Add the src directory to the path so we can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from iftttwh.app import main

if __name__ == "__main__":
    main()