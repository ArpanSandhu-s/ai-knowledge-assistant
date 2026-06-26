"""
core/__init__.py
----------------
Marks `core` as a Python package and ensures the parent directory
is on sys.path so that absolute imports like `from core.agents import ...`
also work when the package is used outside of Streamlit.
"""
import sys
import os

_CORE_DIR   = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_CORE_DIR)

if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)