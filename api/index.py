import sys
import os

# Add project root to path so dashboard.py can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard import app as dash_app

# Vercel expects a WSGI callable named `app`
app = dash_app.server
