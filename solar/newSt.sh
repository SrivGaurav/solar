# 1) (optional) make a safety copy
cp -R solar solar_backup_$(date +%Y%m%d_%H%M%S) || true

# 2) run the refactor
python refactor_solar_repo.py

# 3) (optional) inspect changes
git status

# 4) commit on a new branch
git checkout -b refactor/modular-structure
git add .
git commit -m "Refactor: modular structure, cleaned imports, CLI rename, .gitignore"
git push -u origin refactor/modular-structure

# 5) your zip will be here:
ls -lh solar_refactored.zip
