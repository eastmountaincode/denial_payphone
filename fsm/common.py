"""
Common path setup for all FSM state handlers.
This eliminates the need for repeated path boilerplate in every state file.
Each state should still import its own specific utilities for clarity.
"""

import os
import sys

# Setup paths once - go up two levels from fsm/common.py to reach project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UTIL_DIR = os.path.join(BASE_DIR, "util")

# Add util directory to Python path if not already present
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR) 