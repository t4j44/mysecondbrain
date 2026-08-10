#!/usr/bin/env python3
"""
Automated Database and Storage Backup Script for Taj's Second Brain.
Creates timestamped backups of PostgreSQL schema & data and private storage files.
"""

import os
import sys
import datetime
import subprocess

def run_backup():
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = os.environ.get("BACKUP_DIR", "./backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[!] ERROR: DATABASE_URL environment variable is required for backup.")
        sys.exit(1)
        
    backup_path = os.path.join(backup_dir, f"taj_brain_db_{timestamp}.sql.gz")
    print(f"[*] Starting Supabase PostgreSQL backup to {backup_path}...")
    
    cmd = f"pg_dump '{db_url}' | gzip > '{backup_path}'"
    res = subprocess.run(cmd, shell=True)
    
    if res.returncode == 0:
        print(f"[+] Backup completed successfully: {backup_path}")
    else:
        print(f"[!] ERROR: pg_dump failed with exit code {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    run_backup()
