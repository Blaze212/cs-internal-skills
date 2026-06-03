---
name: skool-redaction-workflow
description: Orchestrator for the full Skool screenshot → proof log pipeline. Discovers images, calls skool-redact-images for redaction, then skool-update-proof-log for uploads and sheet updates. One-command full workflow.
---

# Skool Redaction Workflow

**Complete end-to-end orchestrator.** Discovers Skool screenshots from your inbox, redacts PII, uploads to Drive, and logs proof data to your sheet in one go.

**Trigger on:** "redact skool screenshots", "process screenshot batch", "log wins", "proof log"

---

## Overview

This skill chains two sub-skills:

1. **skool-redact-images** — Redact PII, extract proof data, return redacted PNG and SVG + metadata
2. **skool-update-proof-log** — Upload to Drive, append sheet rows, move files to done folder

---

## Workflow

### Phase 1: Verify config and discover images

```bash
cat ~/.config/skool-automations/proof-log.json 2>/dev/null || echo "NOT FOUND"
```

Show the user the files to process and confirm before proceeding.

### Phase 2: Call skool-redact-images

Invoke the redaction skill with the image list. This:
- Pixel-scans for avatars, names, @mentions
- Renders redacted PNGs and editable SVGs in parallel
- Extracts post text and proof data via vision pass
- Returns per-image JSON with redacted file paths and metadata

### Phase 3: Call skool-update-proof-log

Pass the redaction results to the upload skill. This:
- Uploads original to original folder, redacted PNG + SVG to redacted folder on Google Drive (configurable)
- Extracts full proof log fields (area, level, function, etc.)
- Appends structured rows to the proof sheet
- Moves files to done folder, updates url_index.json

### Phase 4: Summary and timing

Aggregate results and print:
- Per-image status (✅/⚠️/❌)
- Timing breakdown (per-step medians across all images)
- Action items (missing fields, failed uploads, etc.)

---

## Common workflows

**Process all pending screenshots:**
```
Redact my skool screenshots
```

**Process and target specific proof areas:**
```
Redact skool screenshots and log them as Outreach and Sales wins
```

**Check status without processing:**
```
Show me what's in my redaction inbox
```

---

## Troubleshooting

If redaction fails on an image:
- Re-run just that image through `skool-redact-images`
- Check the SVG redacted file to manually adjust redaction regions

If sheet update fails:
- Verify the sheet tab is named "Overview" (check the config)
- Ensure the service account has Editor access to the Drive folder
