#!/usr/bin/env python3
"""
Read and parse the proof-log.json config file with backward compatibility.

Handles:
- New config with driveFolderIdOriginal and driveFolderIdRedacted
- Legacy config with single driveFolderId (both types use same folder)
"""
from __future__ import annotations

import json
import os
import sys


def read_config() -> dict:
    """
    Read ~/.config/skool-automations/proof-log.json.

    Returns dict with keys:
        inboxDir, doneDir, sheetId,
        driveFolderIdOriginal, driveFolderIdRedacted

    Raises if config not found or missing required keys.
    """
    config_path = os.path.expanduser("~/.config/skool-automations/proof-log.json")

    if not os.path.exists(config_path):
        raise RuntimeError(
            f"Config not found: {config_path}\n"
            f"Create it with driveFolderIdOriginal and driveFolderIdRedacted (or legacy driveFolderId)"
        )

    with open(config_path) as f:
        config = json.load(f)

    # Validate required keys
    required = {"inboxDir", "doneDir", "sheetId"}
    missing = required - set(config.keys())
    if missing:
        raise RuntimeError(f"Config missing required keys: {', '.join(missing)}")

    # Handle backward compatibility: if old driveFolderId exists, use it for both
    if "driveFolderId" in config and "driveFolderIdOriginal" not in config:
        config["driveFolderIdOriginal"] = config["driveFolderId"]
        config["driveFolderIdRedacted"] = config["driveFolderId"]

    # Validate folder IDs
    folder_keys = {"driveFolderIdOriginal", "driveFolderIdRedacted"}
    missing_folders = folder_keys - set(config.keys())
    if missing_folders:
        raise RuntimeError(
            f"Config missing folder IDs: {', '.join(missing_folders)}\n"
            f"Add driveFolderIdOriginal and driveFolderIdRedacted to your config"
        )

    return config


if __name__ == "__main__":
    config = read_config()
    print(json.dumps(config, indent=2))
