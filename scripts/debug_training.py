"""
Debug script for ProtoSSM training pipeline.
Run on Vertex AI terminal: python scripts/debug_training.py
Or execute via Jupyter API: python scripts/jupyter_exec.py --file scripts/debug_training.py
"""
import os, sys, re
from pathlib import Path
import numpy as np
import pandas as pd

DATA_ROOT = Path('/home/jupyter/birdclef-2026/data/competition/raw')
CACHE_DIR = Path('/home/jupyter/cache')

print("="*60)
print("STEP 1: Check soundscape files")
ss_dir = DATA_ROOT / 'train_soundscapes'
ss_files = list(ss_dir.glob('*.ogg')) if ss_dir.exists() else []
print(f"  train_soundscapes/ exists: {ss_dir.exists()}")
print(f"  .ogg files found: {len(ss_files)}")
if ss_files:
    print(f"  Sample filenames: {[f.name for f in ss_files[:5]]}")

print()
print("STEP 2: Check soundscape labels CSV")
labels_path = DATA_ROOT / 'train_soundscapes_labels.csv'
if labels_path.exists():
    ss_labels = pd.read_csv(labels_path)
    print(f"  Rows: {len(ss_labels)}")
    print(f"  Columns: {list(ss_labels.columns)}")
    print(f"  Unique filenames: {ss_labels['filename'].nunique()}")
    print(f"  Sample filenames from CSV: {ss_labels['filename'].unique()[:5].tolist()}")
else:
    print("  MISSING: train_soundscapes_labels.csv not found!")

print()
print("STEP 3: Check filename match between CSV and disk")
if ss_files and labels_path.exists():
    csv_fnames = set(ss_labels['filename'].unique())
    disk_fnames = set(f.name for f in ss_files)
    matched = csv_fnames & disk_fnames
    print(f"  CSV filenames: {len(csv_fnames)}")
    print(f"  Disk filenames: {len(disk_fnames)}")
    print(f"  Matched: {len(matched)}")
    if len(matched) == 0:
        print("  ⚠️  NO MATCH — filenames in CSV don't match files on disk!")
        print(f"  CSV example: {list(csv_fnames)[:3]}")
        print(f"  Disk example: {list(disk_fnames)[:3]}")

print()
print("STEP 4: Test parse_fname on actual filenames")
def parse_fname(fname):
    """Parse site and hour from soundscape filename."""
    m = re.match(r'(.+?)_(\d{8})_(\d{6})', Path(fname).stem)
    if m:
        return {'site': m.group(1), 'date': m.group(2), 'hour_utc': int(m.group(3)[:2])}
    # Fallback
    return {'site': Path(fname).stem, 'date': '00000000', 'hour_utc': 0}

if ss_files:
    for f in ss_files[:5]:
        result = parse_fname(f.name)
        print(f"  {f.name} → {result}")

print()
print("STEP 5: Check cache")
cache_files = list(CACHE_DIR.glob('*.npz')) if CACHE_DIR.exists() else []
print(f"  Cache dir exists: {CACHE_DIR.exists()}")
print(f"  Cached .npz files: {len(cache_files)}")
if cache_files:
    sample = np.load(cache_files[0])
    print(f"  Sample cache keys: {list(sample.keys())}")
    print(f"  emb shape: {sample['emb'].shape}, logits shape: {sample['logits'].shape}")

print()
print("STEP 6: Check taxonomy")
tax = pd.read_csv(DATA_ROOT / 'taxonomy.csv')
print(f"  Classes: {len(tax)}")
print(f"  Columns: {list(tax.columns)}")

print()
print("DONE — share this output to diagnose training issues")
