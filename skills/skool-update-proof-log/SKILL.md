---
name: skool-update-proof-log
description: Post-redaction step: upload redacted images to Google Drive, append structured proof log rows to the sheet, move files to done folder, update URL index. Input: redacted images + proof data from skool-redact-images.
---

# Skool Update Proof Log

**Step 2 of redaction workflow.** Takes redacted images and proof data from `skool-redact-images`, uploads files to Google Drive, appends proof log rows to the sheet, and archives files.

**Input:** Redacted PNG, SVG, and proof data from previous step.  
**Output:** Drive URLs, sheet row added, files moved to done folder.

---

## Step 0 — Read config

```bash
cat ~/.config/skool-automations/proof-log.json 2>/dev/null || echo "NOT FOUND"
```

Required keys (same as redaction step):
```json
{
  "inboxDir": "/path/to/to-redact",
  "doneDir": "/path/to/completed",
  "driveFolderIdOriginal": "<Google Drive folder ID for original images>",
  "driveFolderIdRedacted": "<Google Drive folder ID for redacted images>",
  "sheetId": "<Google Sheet ID>"
}
```

Legacy config (driveFolderId) is still supported for backward compatibility — both original and redacted files will use the same folder.

---

## Step 1 — Upload files to Drive

For each redacted image result, upload 3 files using the friendly title (sanitized):

```bash
# Original (unredacted) — to driveFolderIdOriginal
doppler run -- python3 SKILL_DIR/scripts/upload_to_drive.py \
  IMAGE_PATH "<title>.png" DRIVE_FOLDER_ID_ORIGINAL
# → ORIGINAL_URL

# Redacted PNG — to driveFolderIdRedacted
doppler run -- python3 SKILL_DIR/scripts/upload_to_drive.py \
  OUTPUT_DIR/redacted-redacted.png "<title>-redacted.png" DRIVE_FOLDER_ID_REDACTED
# → PNG_URL

# Editable SVG — to driveFolderIdRedacted
doppler run -- python3 SKILL_DIR/scripts/upload_to_drive.py \
  OUTPUT_DIR/redacted-editable.svg "<title>-editable.svg" DRIVE_FOLDER_ID_REDACTED
# → SVG_URL
```

---

## Step 2 — Extract proof data (if not already done)

If proof fields are missing, run:
```bash
PROOF_JSON=$(doppler run -- python3 SKILL_DIR/scripts/extract_proof_data.py "$POST_TEXT")
```

This returns: `area, level, function, status, main_objection, trigger, behavior, outcome, friction_surprise, artifact_candidate`

---

## Step 3 — Append sheet rows

For each image, run:

```bash
doppler run -- python3 <skill-dir>/scripts/append_sheet_row.py \
  "<sheetId>" \
  '<JSON with all proof fields + png_url + svg_url + original_url + date>'
```

The JSON must include:
`date (MM/DD/YYYY), post_url, title, original_filename, png_filename, svg_filename, area, level, function, status, main_objection, trigger, behavior, outcome, friction_surprise, artifact_candidate, post_text, original_url, png_url, svg_url`

The script reads the actual header row and matches columns by name (order doesn't matter).

---

## Step 4 — Move files and update index

```bash
python3 << 'EOF'
import os, shutil, json

cfg = json.load(open(os.path.expanduser('~/.config/skool-automations/proof-log.json')))
inbox = cfg['inboxDir']
done = cfg['doneDir']
idx_path = os.path.join(inbox, 'url_index.json')

# results = list of dicts from redaction step
results = <results from skool-redact-images>

if os.path.exists(idx_path):
    idx = json.load(open(idx_path))
    screenshots = idx.get('screenshots', [])
else:
    idx = {'screenshots': []}
    screenshots = []

for r in results:
    src = os.path.join(inbox, r['source_filename'])
    dest = os.path.join(done, r['original_filename'])
    if os.path.exists(src):
        shutil.move(src, dest)
        print(f"Moved: {r['source_filename']} → {r['original_filename']}")
    
    # Update index entry
    for entry in screenshots:
        if entry.get('filename') == r['source_filename']:
            entry['filename'] = r['original_filename']
            break

with open(idx_path, 'w') as f:
    json.dump(idx, f, indent=2)
print("url_index.json updated")
EOF
```

---

## Step 5 — Summary report

Print a summary table showing upload status and any issues:

```
✅ Outreach Win - Rosh Sharma   → all 3 files uploaded, sheet row added
⚠️  Mindset Win - Day Quinn      → PNG/SVG uploaded, Drive 404 on original
❌  screenshot_xyz.png           → Drive upload failed
⚠️  Mindset Win - John Smith      → PNG/SVG uploaded, status column is unknown
```

List any items needing user action (missing fields, failed uploads, etc.).
