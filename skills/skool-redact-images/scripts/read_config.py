#!/usr/bin/env python3
"""Wrapper that imports read_config from shared lib."""
from __future__ import annotations

import sys
import os

# Add parent skool lib to path
lib_path = os.path.join(os.path.dirname(__file__), "../../../lib")
sys.path.insert(0, lib_path)

from read_config import read_config
import json

if __name__ == "__main__":
    config = read_config()
    print(json.dumps(config, indent=2))
