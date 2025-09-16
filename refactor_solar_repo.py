#!/usr/bin/env python3
import re, shutil, zipfile, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "solar"

if not PKG.exists():
    print(f"❌ Expected {PKG} with your .py files inside.")
    sys.exit(1)

# Clean build junk
def rm(p): 
    if p.exists(): shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink()
for junk in [ROOT/"build", ROOT/"dist", ROOT/"solar_model.egg-info", PKG/"__pycache__", PKG/"build"]:
    rm(junk)

# .gitignore
gi = ROOT/".gitignore"
lines = set(gi.read_text().splitlines()) if gi.exists() else set()
lines |= {"__pycache__/", "*.pyc","*.pyo","*.pyd","*.egg-info/","build/","dist/",".ipynb_checkpoints/",".DS_Store"}
gi.write_text("\n".join(sorted(lines)) + "\n")

# Create subfolders
for sub in ["io","processing","risk","visualization","tests"]:
    (PKG/sub).mkdir(exist_ok=True)

# Move files into their submodules
move_map = {
    "data_input.py":         "io",
    "ssrd_io.py":             "io",
    "ssrd_zarr_adapter.py":   "io",
    "data_processing.py":     "processing",
    "detrending.py":           "processing",
    "gamma_model.py":           "processing",
    "payouts.py":                 "risk",
    "sobol_sim.py":                "risk",
    "plotting.py":                   "visualization",
    "main.py":                        "cli.py",   # rename
}
for name, dest in move_map.items():
    src = PKG/name
    if src.exists():
        if dest.endswith(".py"):
            src.rename(PKG/dest)  # rename main.py -> cli.py
        else:
            src.rename(PKG/dest/name)

# Add __init__.py
for d in [PKG, PKG/"io", PKG/"processing", PKG/"risk", PKG/"visualization"]:
    (d/"__init__.py").touch(exist_ok=True)

# Rewrite imports to use package paths
fq_map = {
    "data_input":"solar.io.data_input","ssrd_io":"solar.io.ssrd_io","ssrd_zarr_adapter":"solar.io.ssrd_zarr_adapter",
    "data_processing":"solar.processing.data_processing","detrending":"solar.processing.detrending","gamma_model":"solar.processing.gamma_model",
    "payouts":"solar.risk.payouts","sobol_sim":"solar.risk.sobol_sim","plotting":"solar.visualization.plotting","config":"solar.config"
}
pattern_from = re.compile(r"^from\s+([a-zA-Z_][\w\.]*)\s+import\s+", re.M)
pattern_import = re.compile(r"^import\s+([a-zA-Z_][\w\.]*)(\s+as\s+\w+)?\s*$", re.M)
def rewrite(txt:str)->str:
    def fr(m):
        b=m.group(1).split(".")[0]
        return f"from {fq_map[b]} import " if b in fq_map and m.group(1)==b else m.group(0)
    def im(m):
        b=m.group(1).split(".")[0]
        a=m.group(2) or ""
        return f"import {fq_map[b]}{a}" if b in fq_map and m.group(1)==b else m.group(0)
    return pattern_import.sub(im, pattern_from.sub(fr, txt))

for f in PKG.rglob("*.py"):
    if f.name=="__init__.py": continue
    t=f.read_text(encoding="utf-8",errors="ignore")
    n=rewrite(t)
    if n!=t: f.write_text(n,encoding="utf-8")

# Zip the package
zip_path = ROOT/"solar_refactored.zip"
with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED) as z:
    for p in PKG.rglob("*"):
        if p.is_file(): z.write(p,p.relative_to(ROOT))
    for n in ["pyproject.toml","setup.cfg","README.md",".gitignore"]:
        p = ROOT/n
        if p.exists(): z.write(p,p.relative_to(ROOT))

print(f"✅ Refactor complete. Zip at {zip_path}")
