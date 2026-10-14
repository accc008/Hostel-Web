import os
import sys

# Ensure parent directory is in Python path for Vercel Serverless environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel Serverless Function entry point
app = app
