#!/usr/bin/env python
"""
Main entry point for Audio-to-Storyboard Video Generator.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.video_generator import main as video_main

if __name__ == "__main__":
    sys.exit(video_main())
