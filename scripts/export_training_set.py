#!/usr/bin/env python3
"""
CVIS Active Learning Dataset Exporter (Phase 7.1)

Exports human-confirmed and rejected body crops along with standardized labels
for heuristic model fine-tuning and retraining.

PRIVACY GUARANTEE:
- Exports ONLY clothing/body crops (body_crop_ref).
- Never exports face crops or biometric identifiers.
- Excludes student PII from the export manifest.
"""

import os
import csv
import shutil
import sqlite3
from pathlib import Path

# Anchored paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DB_FILE = PROJECT_ROOT / "cvis.db"
STORAGE_DIR = PROJECT_ROOT / "storage_data"
EXPORT_DIR = PROJECT_ROOT / "exports" / "training_dataset"
IMAGES_DIR = EXPORT_DIR / "images"
MANIFEST_PATH = EXPORT_DIR / "manifest.csv"

def export_training_dataset():
    if not DB_FILE.exists():
        print(f"[ERROR] Database file not found at: {DB_FILE}")
        return

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, flag_id, body_crop_ref, violation_type, is_violation, 
               rejection_reason, model_version, labeled_by, created_at
        FROM training_examples
    """)
    rows = cursor.fetchall()

    if not rows:
        print("[INFO] No training examples found in training_examples table yet.")
        conn.close()
        return

    manifest_records = []
    copied_count = 0
    missing_count = 0

    for row in rows:
        (t_id, flag_id, body_ref, v_type, is_viol, rej_reason, m_ver, labeled_by, created_at) = row
        
        # Privacy sanity check: ref must not be a face crop
        if "face" in str(body_ref).lower() and "body" not in str(body_ref).lower():
            print(f"[SKIPPED] Potential non-body crop detected: {body_ref}")
            continue

        src_path = STORAGE_DIR / body_ref
        target_filename = f"{t_id}.jpg"
        dest_path = IMAGES_DIR / target_filename

        if src_path.exists():
            shutil.copy2(str(src_path), str(dest_path))
            copied_count += 1
        else:
            missing_count += 1

        manifest_records.append({
            "example_id": t_id,
            "flag_id": flag_id,
            "image_filename": target_filename,
            "violation_type": v_type,
            "is_violation": bool(is_viol),
            "rejection_reason": rej_reason or "N/A",
            "model_version": m_ver,
            "created_at": created_at
        })

    # Write CSV Manifest
    with open(MANIFEST_PATH, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "example_id", "flag_id", "image_filename", "violation_type",
            "is_violation", "rejection_reason", "model_version", "created_at"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for rec in manifest_records:
            writer.writerow(rec)

    conn.close()

    print("==================================================")
    print(" CVIS Active Learning Dataset Export Complete")
    print("==================================================")
    print(f"Total Examples Exported:  {len(manifest_records)}")
    print(f"Image Crops Copied:       {copied_count} (Missing on disk: {missing_count})")
    print(f"Destination Manifest:     {MANIFEST_PATH}")
    print(f"Destination Images Dir:   {IMAGES_DIR}")
    print("==================================================")

if __name__ == "__main__":
    export_training_dataset()
