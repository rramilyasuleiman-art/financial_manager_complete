"""
Configures pytest to add the project root to sys.path.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
