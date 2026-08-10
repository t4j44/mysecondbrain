#!/usr/bin/env python3
"""
Automated Disaster Recovery & Database Restoration Script for Taj's Second Brain.
Restores PostgreSQL dumps while preserving RLS policies and user isolation invariants.
"""

import os
import sys
import subprocess

def restore_backup(backup_file_path: str):
    if not os.path.exists(backup_file_path):
        print(f"[!] ERROR: Specified backup file does not exist: {backup_file_path}")
        sys.exit(1)
        
    target_db_url = os.environ.get("DATABASE_URL")
    if not target_db_url:
        print("[!] ERROR: DATABASE_URL environment variable is required for restoration.")
        sys.exit(1)
        
    print(f"[*] Restoring database from {backup_file_path}...")
    
    if backup_file_path.endswith(".gz"):
        cmd = f"gunzip -c '{backup_file_path}' | psql '{target_db_url}'"
    else:
        cmd = f"psql '{target_db_url}' -f '{backup_file_path}'"
        
    res = subprocess.run(cmd, shell=True)
    
    if res.returncode == 0:
        print("[+] Database restoration completed successfully.")
        print("[*] Verifying RLS policies and extensions...")
        verify_cmd = f"psql '{target_db_url}' -c 'SELECT count(*) FROM pg_tables WHERE schemaname = public AND rowsecurity = true;'"
        subprocess.run(verify_cmd, shell=True)
    else:
        print(f"[!] ERROR: Database restoration failed with code {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore.py <path_to_backup.sql[.gz]>")
        sys.exit(1)
    restore_backup(sys.argv[1])
