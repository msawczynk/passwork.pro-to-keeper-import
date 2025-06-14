#!/usr/bin/env python3
"""
convert-to-keeper-json.py
=========================
Consume a *decrypted* Passwork export produced by `full-export-passwork.py`
and emit a single `keeper-import.json` file that matches Keeper's custom JSON
import schema.  Attachments are inlined as base‑64 blobs, folder structure is
preserved, and a bonus record containing the raw activity log is included.

Usage
-----
$ export PASSWORK_EXPORT_DIR=export      # default is ./export
$ python convert-to-keeper-json.py

Then either:
  • Web Vault:  Settings ▸ Import ▸ Keeper JSON ▸ pick keeper-import.json
  • Commander:  keeper import --format=json keeper-import.json

Requires: Python ≥3.9 (for pathlib) and nothing else.
"""

import os, json, base64, pathlib, sys

BASE = pathlib.Path(os.getenv("PASSWORK_EXPORT_DIR", "export")).expanduser().resolve()
if not BASE.exists():
    sys.exit(f"[!] Export directory {BASE} not found. Set PASSWORK_EXPORT_DIR or run export script first.")

records = []

def slug_path(path: pathlib.Path) -> str:
    """Convert export-relative path into Keeper folder path (backslashes)"""
    return "\".join(path.parts)

# iterate through every decrypted record
for json_path in BASE.rglob("item_*.json"):
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[!] Skipping {json_path} ({e})")
        continue

    rel_folder = json_path.parent.relative_to(BASE)
    folder_path = slug_path(rel_folder)

    rec = {
        "title": data.get("title") or data.get("name") or "Untitled",
        "login": data.get("login") or data.get("username") or "",
        "password": data.get("password") or "",
        "login_url": data.get("url") or data.get("link") or "",
        "notes": data.get("description") or data.get("notes") or "",
        "custom_fields": {cf["name"]: cf.get("value", "") for cf in data.get("customFields", [])},
        "folders": [{"folder": folder_path}],
    }

    # One‑time‑code / TOTP seed if present
    if data.get("totp"):
        rec.setdefault("custom_fields", {})["$oneTimeCode"] = data["totp"]

    # inline attachments
    attach_dir = json_path.parent / "attachments"
    if attach_dir.exists():
        files=[]
        for p in attach_dir.iterdir():
            try:
                files.append({
                    "name": p.name,
                    "data": base64.b64encode(p.read_bytes()).decode()
                })
            except Exception as e:
                print(f"[!] Could not encode attachment {p}: {e}")
        if files:
            rec["files"] = files

    records.append(rec)

# add activity log as a single record
log_path = BASE / "activity_logs.json"
if log_path.exists():
    rec = {
        "title": "Passwork Activity Log",
        "login": "",
        "password": "",
        "notes": "Original activity_logs.json from Passwork export",
        "custom_fields": {},
        "folders": [{"folder": "Passwork_Archive"}],
        "files": [{
            "name": "activity_logs.json",
            "data": base64.b64encode(log_path.read_bytes()).decode()
        }]
    }
    records.append(rec)

output = pathlib.Path("keeper-import.json")
output.write_text(json.dumps({"records": records}, indent=2, ensure_ascii=False))
print(f"[✓] Wrote {output} with {len(records)} records.")
