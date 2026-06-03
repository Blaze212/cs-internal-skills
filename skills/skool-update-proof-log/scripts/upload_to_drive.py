#!/usr/bin/env python3
"""
Upload a single file to a Google Drive folder.

Usage:
    python3 upload_to_drive.py <local_path> <drive_filename> <folder_id>

Credentials: Reads GOOGLE_SERVICE_ACCOUNT_JSON from the environment, or falls back to
credentials.json in the same directory as this script.

Prints the webViewLink to stdout on success.

Supports both My Drive and Shared Drives (supportsAllDrives=True).
"""
from __future__ import annotations

import io
import json
import mimetypes
import os
import sys

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2.service_account import Credentials
except ImportError:
    import subprocess
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install",
         "google-api-python-client", "google-auth",
         "--break-system-packages", "-q"]
    )
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_credentials_json() -> str:
    """Get service account JSON from env var or local credentials.json file."""
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        return sa_json

    # Check for credentials.json in the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(script_dir, "credentials.json")
    if os.path.exists(cred_path):
        with open(cred_path) as f:
            return f.read()

    raise RuntimeError(
        "GOOGLE_SERVICE_ACCOUNT_JSON env var not set and credentials.json not found "
        f"in {script_dir}"
    )


def upload(local_path: str, drive_name: str, folder_id: str) -> str:
    sa_json = _get_credentials_json()

    creds = Credentials.from_service_account_info(
        json.loads(sa_json), scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)

    mime = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    with open(local_path, "rb") as fh:
        data = fh.read()

    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime, resumable=False)
    file_meta = {"name": drive_name, "parents": [folder_id]}

    result = (
        service.files()
        .create(
            body=file_meta,
            media_body=media,
            fields="id,webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )

    link = result.get("webViewLink")
    if not link:
        raise RuntimeError(f"Drive upload returned no webViewLink: {result}")
    return link


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: upload_to_drive.py <local_path> <drive_filename> <folder_id>",
            file=sys.stderr,
        )
        return 1
    local_path, drive_name, folder_id = sys.argv[1], sys.argv[2], sys.argv[3]
    link = upload(local_path, drive_name, folder_id)
    print(link)
    return 0


if __name__ == "__main__":
    sys.exit(main())
