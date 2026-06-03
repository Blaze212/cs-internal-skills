---
name: skool-redact-images
description: Redact avatars, names, and @mentions from Skool screenshots. Auto-discovers images, generates redaction specs via pixel-scanning, applies vision labels, renders redacted PNGs and editable SVGs. Returns per-image redaction output with verification results.
---

# Skool Redact Images

**Step 1 of redaction workflow.** Redacts PII (avatars, names, @mentions) from Skool screenshots and returns redacted images + data needed for the next step (proof log upload).

**Input:** Images in inbox folder (from config).  
**Output:** Redacted PNG, editable SVG, proof-extraction data (post text, friendly title), per-image results JSON.

---

## Step 0 — Read config

```bash
cat ~/.config/skool-automations/proof-log.json 2>/dev/null || echo "NOT FOUND"
```

Required keys:
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

## Step 1 — Discover images and load URL index

```bash
python3 -c "
import os, json
cfg = json.load(open(os.path.expanduser('~/.config/skool-automations/proof-log.json')))
inbox = cfg['inboxDir']
files = sorted(f for f in os.listdir(inbox) if f.lower().endswith(('.png','.jpg','.jpeg')))
idx_path = os.path.join(inbox, 'url_index.json')
url_map = {}
if os.path.exists(idx_path):
    idx = json.load(open(idx_path))
    url_map = {s['filename']: s['url'] for s in idx.get('screenshots', [])}
for f in files:
    url = url_map.get(f, 'NOT FOUND')
    print(f'{f}  →  {url}')
"
```

Show the list to the user and confirm before proceeding.

---

## Step 2 — Spawn parallel Haiku subagents (redaction)

**One Agent tool call. All subagents in the same message. Model: haiku.**

For each image, compute:
- `SLUG` — `pathlib.Path(filename).stem` with spaces/unicode replaced by `-`
- `OUTPUT_DIR` — `<skill-dir>/outputs/<SLUG>/`
- `POST_URL` — from the url_index.json map (empty string if not found)

### Subagent template

```
You are redacting one Skool screenshot.

IMAGE_PATH:      <absolute path to image>
SLUG:            <sanitized stem>
OUTPUT_DIR:      <skill-dir>/outputs/<slug>/
SKILL_DIR:       <skill-dir>
POST_URL:        <url from url_index.json, or empty string>

GOOGLE_SERVICE_ACCOUNT_JSON is in the environment — prefix every script call with:
  doppler run --

---

### A — Setup
mkdir -p OUTPUT_DIR
T0=$(python3 -c "import time; print(time.time())")

### B — Pixel-scan redaction spec
cd SKILL_DIR && python3 scripts/build_spec.py IMAGE_PATH OUTPUT_DIR/spec.json
cd SKILL_DIR && python3 scripts/find_blue_pixels.py IMAGE_PATH 80
# (Add custom regions for any missed @mentions)
T_B=$(python3 -c "import time; print(round(time.time() - $T0, 1))")

### C — Add labels (vision pass)
# Read IMAGE_PATH visually. Replace every "Person N — add label" with the real name.
T_C=$(python3 -c "import time; print(round(time.time() - $T0, 1))")

### D — Render
cd SKILL_DIR
python3 scripts/build_svg.py IMAGE_PATH OUTPUT_DIR/spec.json OUTPUT_DIR/redacted-editable.svg
python3 scripts/render_redactions.py IMAGE_PATH OUTPUT_DIR/redacted-redacted.png OUTPUT_DIR/spec.json
T_D=$(python3 -c "import time; print(round(time.time() - $T0, 1))")

### E — Verify (max 3 attempts)
cd SKILL_DIR && python3 scripts/verify_redactions.py IMAGE_PATH OUTPUT_DIR/redacted-final.png OUTPUT_DIR/spec.json
# If fails: fix spec.json → re-render → re-verify (max 3 times)
T_E=$(python3 -c "import time; print(round(time.time() - $T0, 1))")

### F — Visual check
# Read OUTPUT_DIR/redacted-final.png. Confirm avatars, names, @mentions, timestamps all correct.
T_F=$(python3 -c "import time; print(round(time.time() - $T0, 1))")

### G — Extract proof data (vision pass)
# Read IMAGE_PATH visually.
# Transcribe full post text (all paragraphs, preserve line breaks as \n).
# Extract the poster's first name from the post/profile (NOT hardcoded).
# Generate friendly title: "<area> Win - <first_name>" where first_name comes from the image.
# Example: "Outreach Win - Rosh" (not "Outreach Win - Barton")
POST_TEXT="<transcribed text from image>"
FRIENDLY_TITLE="<area_from_post> Win - <poster_first_name_from_image>"

### Return result
Print this exact JSON as the LAST thing. **This JSON will be used directly by the orchestrator—do not hardcode or substitute values.**

```json
{
  "slug": "SLUG",
  "source_filename": "<original filename>",
  "post_url": "POST_URL",
  "original_filename": "<FRIENDLY_TITLE>.png",
  "png_filename": "<FRIENDLY_TITLE>-redacted.png",
  "svg_filename": "<FRIENDLY_TITLE>-editable.svg",
  "warnings": [],
  "timing": { "B_spec": "X", "C_labels": "X", "D_render": "X", "E_verify": "X", "F_visual": "X", "G_proof": "X", "total": "X" },
  "extracted": {
    "poster_first_name": "<extracted from image>",
    "poster_full_name": "<extracted from image>",
    "post_text": "<transcribed from image>",
    "post_title": "<extracted from image>",
    "area": "<inferred from post, or 'unknown'>",
    "level": "<inferred from post, or 'unknown'>",
    "function": "<inferred from post, or 'unknown'>",
    "status": "<inferred from post, or 'unknown'>",
    "trigger": "<inferred from post, or 'unknown'>",
    "behavior": "<inferred from post, or 'unknown'>",
    "outcome": "<inferred from post, or 'unknown'>",
    "friction_surprise": "<inferred from post, or 'unknown'>",
    "artifact_candidate": "<inferred from post, or 'unknown'>"
  },
  "confidence": {
    "poster_name": "high|medium|low",
    "post_text": "high|medium|low",
    "area": "high|medium|low",
    "level": "high|medium|low"
  }
}
```

**Important:** All extracted values come from reading the image, never from hardcoded defaults. Fields marked `"unknown"` will be flagged by the proof log reporter.
```

---

## Step 3 — Return results

Collect result JSON from each subagent. Print a summary table:

```
✅ Outreach Win - Rosh          → redacted, proof data extracted
⚠️  Mindset Win - Day           → redacted, verify FAIL on name bbox
❌  screenshot_xyz.png           → redaction failed: [error]
```

Pass all result JSONs to the next skill: `skool-update-proof-log`.
