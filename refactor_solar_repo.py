#!/usr/bin/env python3
import os, re, shutil, zipfile, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG_OLD = ROOT / "solar" / "solar"    # your current code location
PKG_NEW = ROOT / "solar"              # target package location

# Sanity checks
if not PKG_OLD.exists():
    print(f"❌ Expected source at {PKG_OLD} but it wasn’t found.\n"
          f"Tip: ensure you run this script in the repo root that contains 'solar/solar/'.")
    sys.exit(1)

# 1) Clean build junk (but only from VCS workspace — safe to recreate later)
def rm(p):
    if p.exists():
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        else:
            p.unlink(missing_ok=True)

for junk in [
    ROOT/"build", ROOT/"dist",
    ROOT/"solar_model.egg-info",
    ROOT/".ipynb_checkpoints",
    PKG_OLD/"__pycache__",
    ROOT/"solar"/"build",
]:
    rm(junk)

# 2) Ensure .gitignore has the right entries
gi = ROOT/".gitignore"
gi_lines = set()
if gi.exists():
    gi_lines = set(gi.read_text().splitlines())

needed = {
"__pycache__/",
"*.pyc",
"*.pyo",
"*.pyd",
"*.egg-info/",
"build/",
"dist/",
".ipynb_checkpoints/",
".DS_Store",
}
gi_lines |= needed
gi.write_text("\n".join(sorted(gi_lines)) + "\n")

# 3) Create new modular folders
(PKG_NEW/"io").mkdir(parents=True, exist_ok=True)
(PKG_NEW/"processing").mkdir(parents=True, exist_ok=True)
(PKG_NEW/"risk").mkdir(parents=True, exist_ok=True)
(PKG_NEW/"visualization").mkdir(parents=True, exist_ok=True)
(PKG_NEW/"tests").mkdir(parents=True, exist_ok=True)

# 4) Files mapping: source -> destination
move_map = {
    "data_input.py":         PKG_NEW/"io"/"data_input.py",
    "ssrd_io.py":            PKG_NEW/"io"/"ssrd_io.py",
    "ssrd_zarr_adapter.py":  PKG_NEW/"io"/"ssrd_zarr_adapter.py",

    "data_processing.py":    PKG_NEW/"processing"/"data_processing.py",
    "detrending.py":         PKG_NEW/"processing"/"detrending.py",
    "gamma_model.py":        PKG_NEW/"processing"/"gamma_model.py",

    "payouts.py":            PKG_NEW/"risk"/"payouts.py",
    "sobol_sim.py":          PKG_NEW/"risk"/"sobol_sim.py",

    "plotting.py":           PKG_NEW/"visualization"/"plotting.py",

    "config.py":             PKG_NEW/"config.py",
    "app.py":                PKG_NEW/"app.py",
    "main.py":               PKG_NEW/"cli.py",   # rename
    "__init__.py":           PKG_NEW/"__init__.py",
    "Sobol.csv":             PKG_NEW/"Sobol.csv",  # keep handy for now
}

# 5) Move files according to mapping (overwrite if re-run)
for name, dest in move_map.items():
    src = PKG_OLD/name
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

# 6) Touch __init__.py in each package dir
for d in [PKG_NEW, PKG_NEW/"io", PKG_NEW/"processing", PKG_NEW/"risk", PKG_NEW/"visualization"]:
    (d/"__init__.py").touch(exist_ok=True)

# 7) Rewrite imports inside all .py under new package
# Map of simple module names to fully-qualified paths
fq_map = {
    # io
    "data_input": "solar.io.data_input",
    "ssrd_io": "solar.io.ssrd_io",
    "ssrd_zarr_adapter": "solar.io.ssrd_zarr_adapter",

    # processing
    "data_processing": "solar.processing.data_processing",
    "detrending": "solar.processing.detrending",
    "gamma_model": "solar.processing.gamma_model",

    # risk
    "payouts": "solar.risk.payouts",
    "sobol_sim": "solar.risk.sobol_sim",

    # viz
    "plotting": "solar.visualization.plotting",

    # root
    "config": "solar.config",
}

py_files = list(PKG_NEW.rglob("*.py"))
import_pattern_from = re.compile(r"^from\s+([a-zA-Z_][\w\.]*)\s+import\s+", re.M)
import_pattern_import = re.compile(r"^import\s+([a-zA-Z_][\w\.]*)(\s+as\s+\w+)?\s*$", re.M)

def rewrite_imports(text: str) -> str:
    # Handle 'from X import ...'
    def _from_repl(m):
        mod = m.group(1)
        base = mod.split(".")[0]
        if base in fq_map and mod == base:
            return f"from {fq_map[base]} import "
        return m.group(0)

    # Handle 'import X'
    def _import_repl(m):
        mod = m.group(1)
        alias = m.group(2) or ""
        base = mod.split(".")[0]
        if base in fq_map and mod == base:
            return f"import {fq_map[base]}{alias}"
        return m.group(0)

    text = import_pattern_from.sub(_from_repl, text)
    text = import_pattern_import.sub(_import_repl, text)
    return text

for f in py_files:
    # Don’t rewrite third-party imports; our regex is conservative (module name only)
    # Skip __init__.py: often only package exports.
    if f.name == "__init__.py":
        continue
    txt = f.read_text(encoding="utf-8", errors="ignore")
    new = rewrite_imports(txt)
    if new != txt:
        f.write_text(new, encoding="utf-8")

# 8) Remove old duplicated code directory if empty remnants exist
# (We COPY2 above to be safe; you can switch to move if you prefer)
# Leave the original 'solar/solar' for manual review or remove now:
# shutil.rmtree(PKG_OLD, ignore_errors=True)

# 9) Ensure Streamlit app imports are FQN
app_py = PKG_NEW/"app.py"
if app_py.exists():
    txt = app_py.read_text(encoding="utf-8", errors="ignore")
    new = rewrite_imports(txt)
    if new != txt:
        app_py.write_text(new, encoding="utf-8")

# 10) Zip the refactored package + key project files
zip_path = ROOT/"solar_refactored.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    # include package
    for p in PKG_NEW.rglob("*"):
        if p.is_file():
            z.write(p, p.relative_to(ROOT))

    # include top-level metadata files if present
    for name in ["pyproject.toml", "setup.cfg", "README.md", "app.py", ".gitignore", "testsolar.csv", "Sobol.csv"]:
        p = ROOT/name
        if p.exists():
            z.write(p, p.relative_to(ROOT))

print(f"✅ Refactor complete.\n- New modular package at: {PKG_NEW}\n- Zip created: {zip_path}")
