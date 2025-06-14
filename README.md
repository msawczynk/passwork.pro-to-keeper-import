# Passwork Full Export

> One-shot vacuum that **decrypts and dumps _everything_** from your Passwork
> tenant – vaults, folders, items, attachments, audit logs.  
> Output: a plaintext directory tree under `export/`.

## TL;DR

```bash
git clone https://github.com/your-org/passwork-export.git
cd passwork-export
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# set creds; use a .env if you’re civilised
export PASSWORK_URL="https://company.passwork.pro"
export PASSWORK_API_KEY="pk_live_…"
export PASSWORK_MASTER_PASSWORD="correct-horse-battery-staple"

python full-export-passwork.py
```

## What You Get

```
export/
├── activity_logs.json          # every audit event your account can see
└── <Vault Name>/
    └── <Folder …>/
        ├── item_<uuid>.json    # decrypted record (URL, login, notes, etc.)
        └── attachments/
            └── <filename>      # decrypted binary
```

The script prints a running tally so you know it hasn’t stalled.

## Why Not Use the Built-in Export?

Because the Passwork UI omits deleted attachments and is allergic to large
vaults.  This script hits the REST API directly, decrypts client-side, and
grabs **literally every byte** you have rights to.

## Security Warning (don’t be that person)

1. `export/` holds secrets in plaintext.  **Do not** git-add it.  
2. Run on a machine you control, offline if possible.  
3. Shred the output when you’re done.

## Incremental Sync (future-proofing)

If you need regular backups, wrap the API calls with `updatedFrom` timestamps
and store a cursor file.  Throw a thread-pool around attachment downloads and
the thing flies.

## License

MIT – because lock-in is bad.  See `LICENSE`.

## Opinions, Bugs, PRs

I wrote this because the official exporter didn’t cut it.  If you find issues,
open one.  If you break your vault, that’s on you.
