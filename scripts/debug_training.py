"""Debug script for ProtoSSM training pipeline."""
import os, sys, re
from pathlib import Path
import numpy as np
import pandas as pd

DATA_ROOT = Path('/home/jupyter/birdclef-2026/data/competition/raw')
CACHE_DIR = Path('/home/jupyter/cache')

print("="*60)
print("STEP 1: Soundscape labeled data coverage")
labels_path = DATA_ROOT / 'train_soundscapes_labels.csv'
ss_labels = pd.read_csv(labels_path)
taxonomy = pd.read_csv(DATA_ROOT / 'taxonomy.csv')
PRIMARY_LABELS = taxonomy['primary_label'].tolist()
classes_in_labels = ss_labels['primary_label'].nunique()
print(f"  Total annotation rows: {len(ss_labels)}")
print(f"  Classes with ≥1 annotation: {classes_in_labels} / {len(PRIMARY_LABELS)}")
print(f"  Classes with 0 annotations: {len(PRIMARY_LABELS) - classes_in_labels}")
counts = ss_labels['primary_label'].value_counts()
print(f"  Median annotations per class: {counts.median():.1f}")
print(f"  Max: {counts.max()}, Min: {counts.min()}")

print()
print("STEP 2: train_audio + train.csv coverage")
train_csv = DATA_ROOT / 'train.csv'
train_df = pd.read_csv(train_csv)
print(f"  train.csv rows: {len(train_df)}")
print(f"  Columns: {list(train_df.columns)}")
print(f"  Sample primary_label: {train_df['primary_label'].head(3).tolist()}")
print(f"  Sample filename: {train_df['filename'].head(3).tolist()}")

# Map inat_taxon_id → competition primary_label
tax_map = taxonomy.set_index('inat_taxon_id')['primary_label'].to_dict()
train_df['comp_label'] = train_df['primary_label'].map(tax_map)
mapped = train_df['comp_label'].notna().sum()
print(f"  Clips mapping to competition classes: {mapped} / {len(train_df)}")
print(f"  Unique competition classes covered: {train_df['comp_label'].nunique()} / {len(PRIMARY_LABELS)}")

# Classes with low data
counts2 = train_df['comp_label'].value_counts()
print(f"  Median clips per class: {counts2.median():.1f}")
print(f"  Classes with <5 clips: {(counts2 < 5).sum()}")

print()
print("STEP 3: Check cache location")
for cache_path in [Path('/home/jupyter/cache'), Path('/home/jupyter/birdclef-2026/cache'), Path('cache')]:
    n = len(list(cache_path.glob('*.npz'))) if cache_path.exists() else 0
    print(f"  {cache_path}: exists={cache_path.exists()}, npz_files={n}")

print()
print("STEP 4: train_audio directory")
audio_dir = DATA_ROOT / 'train_audio'
n_species_dirs = len(list(audio_dir.iterdir())) if audio_dir.exists() else 0
n_clips = sum(1 for _ in audio_dir.rglob('*.ogg')) if audio_dir.exists() else 0
print(f"  train_audio/ exists: {audio_dir.exists()}")
print(f"  Species subdirs: {n_species_dirs}")
print(f"  Total .ogg clips: {n_clips}")
