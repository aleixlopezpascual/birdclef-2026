"""
Create EoS-9 notebook: Raunak V6 + class-group-aware fit_prior_tables calibration.

Key change vs ported-raunak-v6-v1:
  After the ResidualSSM correction (test path) and after first_pass_tr (train path),
  apply a class-group-aware prior delta using vectorized prior_logits_vectorized:
    - Birds (Aves, Mammalia, Reptilia): delta_lambda = +0.15  -> net ~0.65
    - Texture (Amphibia, Insecta):       delta_lambda = -0.20  -> net ~0.30

Internal apply_prior(lambda=0.5) stays unchanged so MLP probe training is unaffected.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent

SRC_NB = ROOT / "experiments/kaggle_submission/ported-raunak-v6-v1/ported_raunak_v6_v1.ipynb"
DST_DIR = ROOT / "experiments/kaggle_submission/eos9-prior-calib-v1"
DST_NB = DST_DIR / "eos9_prior_calib_v1.ipynb"

# New helpers injected after apply_prior definition
NEW_HELPERS = "\n".join([
    "",
    "        # ── EoS-9: vectorized prior logits + class-aware calibration ────────────────",
    "        def prior_logits_vectorized(sites, hours, tables, eps=1e-4):",
    "            # Vectorized site/hour prior logits lookup (no Python loops).",
    "            # Returns additive logit correction of shape (n, N_CLASSES).",
    "            n = len(sites)",
    "            p = np.repeat(tables['global_p'][None, :], n, axis=0).astype(np.float32, copy=True)",
    "",
    "            site_idx = np.array([tables['site_to_i'].get(str(s), -1) for s in sites], dtype=np.int32)",
    "            hour_idx = np.array(",
    "                [tables['hour_to_i'].get(int(h), -1) if int(h) >= 0 else -1 for h in hours],",
    "                dtype=np.int32,",
    "            )",
    "            sh_idx = np.array(",
    "                [",
    "                    tables['sh_to_i'].get((str(s), int(h)), -1) if int(h) >= 0 else -1",
    "                    for s, h in zip(sites, hours)",
    "                ],",
    "                dtype=np.int32,",
    "            )",
    "",
    "            valid = hour_idx >= 0",
    "            if valid.any():",
    "                nh = tables['hour_n'][hour_idx[valid]][:, None]",
    "                wh = nh / (nh + 8.0)",
    "                p[valid] = wh * tables['hour_p'][hour_idx[valid]] + (1.0 - wh) * p[valid]",
    "",
    "            valid = site_idx >= 0",
    "            if valid.any():",
    "                ns = tables['site_n'][site_idx[valid]][:, None]",
    "                ws = ns / (ns + 8.0)",
    "                p[valid] = ws * tables['site_p'][site_idx[valid]] + (1.0 - ws) * p[valid]",
    "",
    "            valid = sh_idx >= 0",
    "            if valid.any():",
    "                nsh = tables['sh_n'][sh_idx[valid]][:, None]",
    "                wsh = nsh / (nsh + 4.0)",
    "                p[valid] = wsh * tables['sh_p'][sh_idx[valid]] + (1.0 - wsh) * p[valid]",
    "",
    "            np.clip(p, eps, 1.0 - eps, out=p)",
    "            return (np.log(p) - np.log1p(-p)).astype(np.float32)",
    "",
    "        # Build the boolean class-type mask from taxonomy (already loaded above).",
    "        # TEXTURE_TAXA = {'Amphibia', 'Insecta'} is defined earlier in this cell.",
    "        IS_TEXTURE_CLASS = np.array(",
    "            [CLASS_NAME_MAP.get(lbl, 'Aves') in TEXTURE_TAXA for lbl in PRIMARY_LABELS],",
    "            dtype=bool,",
    "        )",
    "",
    "        # Delta-lambda values (applied ON TOP of the existing apply_prior lambda=0.5).",
    "        # Net effective prior per class group:",
    "        #   Aves/Mammalia/Reptilia: 0.5 + 0.15 = 0.65",
    "        #   Amphibia/Insecta:       0.5 - 0.20 = 0.30",
    "        DELTA_LAMBDA_EVENT   =  0.15",
    "        DELTA_LAMBDA_TEXTURE = -0.20",
    "",
    "        def apply_prior_delta_class_aware(scores, sites, hours, tables):",
    "            # Apply class-group-aware prior delta to raw logit scores.",
    "            # Adds DELTA_LAMBDA_EVENT * prior to event classes and",
    "            # DELTA_LAMBDA_TEXTURE * prior to texture classes.",
    "            delta_prior = prior_logits_vectorized(sites, hours, tables)",
    "            lam = np.where(IS_TEXTURE_CLASS, DELTA_LAMBDA_TEXTURE, DELTA_LAMBDA_EVENT)[None, :]",
    "            return (scores + lam * delta_prior).astype(np.float32)",
    "",
    "        # ── end EoS-9 helpers ────────────────────────────────────────────────────────",
    "",
]) + "\n"

# Training-path prior delta call (inserted before train_probs_for_calib = sigmoid(...))
TRAIN_DELTA_CALL = "\n".join([
    "        # EoS-9: class-aware prior delta on training logits (keeps threshold calibration consistent)",
    "        first_pass_tr = apply_prior_delta_class_aware(",
    "            first_pass_tr, sites=meta_tr[\"site\"].to_numpy(),",
    "            hours=meta_tr[\"hour_utc\"].to_numpy(), tables=prior_tables)",
    "        ",
]) + "\n"

# Test-path prior delta call (inserted after final_scores computation, before temperature scale)
TEST_DELTA_CALL = "\n".join([
    "        # EoS-9: class-aware prior delta on test logits (after ResidualSSM, before sigmoid)",
    "        final_scores = apply_prior_delta_class_aware(",
    "            final_scores, sites=meta_te[\"site\"].to_numpy(),",
    "            hours=meta_te[\"hour_utc\"].to_numpy(), tables=prior_tables)",
    "        ",
]) + "\n"


def _inject_helpers(src: str) -> str:
    """Insert new helpers after the apply_prior function definition."""
    marker = "            return out.astype(np.float32)\n        \n        def file_confidence_scale"
    if marker not in src:
        raise ValueError("Could not find apply_prior end marker in source")
    insert_pos = src.index(marker) + len("            return out.astype(np.float32)\n        \n")
    return src[:insert_pos] + NEW_HELPERS + src[insert_pos:]


def _inject_train_delta(src: str) -> str:
    """Insert training-path prior delta call right before train_probs_for_calib = sigmoid(...)."""
    marker = "        train_probs_for_calib = sigmoid(first_pass_tr)\n"
    if marker not in src:
        raise ValueError("Could not find train_probs_for_calib marker in source")
    insert_pos = src.index(marker)
    return src[:insert_pos] + TRAIN_DELTA_CALL + src[insert_pos:]


def _inject_test_delta(src: str) -> str:
    """Insert test-path prior delta call right after final_scores = first_pass_flat + correction."""
    marker = "        final_scores    = first_pass_flat + correction_weight * correction_flat\n"
    if marker not in src:
        raise ValueError("Could not find final_scores marker in source")
    insert_pos = src.index(marker) + len(marker)
    return src[:insert_pos] + TEST_DELTA_CALL + src[insert_pos:]


def main():
    print(f"Reading source notebook: {SRC_NB}")
    with open(SRC_NB) as f:
        nb = json.load(f)

    # Locate the Model_7 cell
    model7_cell_idx = None
    for i, cell in enumerate(nb["cells"]):
        src = "".join(cell["source"])
        if "if 'Model_7' in _ensemble_models:" in src and "Karnakbayev_PowerOptimization" in src:
            model7_cell_idx = i
            break
    if model7_cell_idx is None:
        raise ValueError("Could not find Model_7 cell in source notebook")
    print(f"Found Model_7 cell at index {model7_cell_idx}")

    src = "".join(nb["cells"][model7_cell_idx]["source"])

    # Apply the three surgical insertions
    src = _inject_helpers(src)
    src = _inject_train_delta(src)
    src = _inject_test_delta(src)

    # Write back as list of lines (Jupyter convention)
    nb["cells"][model7_cell_idx]["source"] = src.splitlines(keepends=True)

    # Update notebook metadata to reflect new name
    nb.setdefault("metadata", {}).setdefault("kernelspec", {})
    nb["metadata"]["kernelspec"]["display_name"] = "EoS-9 Prior Calib v1"

    DST_DIR.mkdir(parents=True, exist_ok=True)
    with open(DST_NB, "w") as f:
        json.dump(nb, f, indent=1)
    print(f"Written: {DST_NB}")

    # Verify injections
    with open(DST_NB) as f:
        nb2 = json.load(f)
    cell_src = "".join(nb2["cells"][model7_cell_idx]["source"])
    checks = [
        ("prior_logits_vectorized", "prior_logits_vectorized function"),
        ("IS_TEXTURE_CLASS", "IS_TEXTURE_CLASS mask"),
        ("DELTA_LAMBDA_EVENT", "DELTA_LAMBDA_EVENT constant"),
        ("apply_prior_delta_class_aware", "apply_prior_delta_class_aware function"),
        ("first_pass_tr = apply_prior_delta_class_aware", "training-path delta call"),
        ("final_scores = apply_prior_delta_class_aware", "test-path delta call"),
    ]
    all_ok = True
    for needle, label in checks:
        ok = needle in cell_src
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {label}")
        if not ok:
            all_ok = False
    if not all_ok:
        raise RuntimeError("One or more injections failed — check the source markers")
    print("All injection checks passed.")


if __name__ == "__main__":
    main()
