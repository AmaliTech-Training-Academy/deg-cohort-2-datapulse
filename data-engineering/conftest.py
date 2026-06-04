import sys
import os
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add pipeline to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pipeline"))
