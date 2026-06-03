#!/usr/bin/env python3
"""Wrapper that imports append_sheet_row from shared lib."""
from __future__ import annotations

import sys
import os

# Add parent skool lib to path
lib_path = os.path.join(os.path.dirname(__file__), "../../../lib")
sys.path.insert(0, lib_path)

from append_sheet_row import main

if __name__ == "__main__":
    sys.exit(main())
