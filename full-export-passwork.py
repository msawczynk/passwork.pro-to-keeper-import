#!/usr/bin/env python3
"""
full-export-passwork.py
=======================

Pulls **all** data from a Passwork instance and drops it into an
`export/` folder that mirrors the vault‑folder structure.

What you get
------------
│── export/
│   ├── activity_logs.json        # every event the API will give you
│   └── <vault_name>/
│       └── <folder …>/
│           ├── item_<uuid>.json  # decrypted record data
│           └── attachments/
│               └── <filename>    # decrypted binary files

Usage
-----
$ export PASSWORK_URL="https://company.passwork.pro"
$ export PASSWORK_API_KEY="xxxxxxxxxxxxxxxx"
$ export PASSWORK_MASTER_PASSWORD="correct‑horse‑battery‑staple"
$ python3 full-export-passwork.py
"""

import os, json, pathlib
from passwork import PassworkClient   # pip install git+https://github.com/passwork-me/passwork-python.git

BASE_DIR = pathlib.Path("export").resolve()
BASE_DIR.mkdir(exist_ok=True)

url       = os.environ["PASSWORK_URL"].rstrip("/")
api_key   = os.environ["PASSWORK_API_KEY"]
master_pw = os.environ["PASSWORK_MASTER_PASSWORD"]

client = PassworkClient(url, verify_tls=True)
client.authorize(api_key, master_pw)          # handles token exchange + key derivation

def safe(name: str) -> str:
    """Return filesystem‑safe slug."""
    return "".join(c for c in name if c.isalnum() or c in "._- ")[:64]

def dump_json(path: pathlib.Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

print("▶ listing vaults …")
for vault in client.get_vaults()["items"]:
    v_id   = vault["id"]
    v_name = safe(vault["name"])
    v_root = BASE_DIR / v_name
    print(f"  └─ vault {v_name} ({v_id})")

    # breadth‑first walk of folders
    queue = [(None, v_root)]  # (folder_id, path)

    while queue:
        f_id, f_dir = queue.pop(0)
        f_dir.mkdir(parents=True, exist_ok=True)

        # subfolders
        for sub in client.get_folders({"vaultId": v_id, "parentId": f_id})["items"]:
            queue.append((sub["id"], f_dir / safe(sub["name"])) )

        # items
        for it in client.get_items({"vaultId": v_id, "folderId": f_id})["items"]:
            it_id = it["id"]
            raw   = client.get_item(it_id)      # decrypted by connector
            dump_json(f_dir / f"item_{it_id}.json", raw)

            # attachments
            if raw.get("attachments"):
                a_dir = f_dir / "attachments"
                a_dir.mkdir(exist_ok=True)
                for a in raw["attachments"]:
                    att_id   = a["id"]
                    att_name = safe(a["name"])
                    print(f"      ↳ attachment {att_name}")
                    blob = client.get_item_attachment(it_id, att_id)
                    (a_dir / att_name).write_bytes(blob)

print("▶ pulling activity logs …")
logs = client.call("GET", "/api/v1/activity_logs")["items"]
dump_json(BASE_DIR / "activity_logs.json", logs)

print("✔ finished.  Data saved under", BASE_DIR)
