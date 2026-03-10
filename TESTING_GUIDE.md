# Manual Testing Guide for conflict_parser

## Quick Test Method

### 1. Create Conflicts Manually
```bash
# In your git repository
git checkout -b test-conflicts
echo "Feature branch content" > test.txt
git add test.txt
git commit -m "Add feature content"

git checkout main
echo "Main branch content" > test.txt
git add test.txt
git commit -m "Add main content"

git merge test-conflicts  # This will create conflicts
```

### 2. Run the Test Script
```bash
python test_conflict_parser.py
```

### 3. Test in Python REPL
```python
from fancygit import FancyGit
fg = FancyGit()
conflicts = fg.conflict_parser()
for conflict in conflicts:
    print(f"File: {conflict.file}, Line: {conflict.line}, Message: {conflict.message}")
```

### 4. Check Repository State
```python
from fancygit import FancyGit
fg = FancyGit()
state = fg.get_repo_state()
print(f"Conflicting files: {state['conflicts']}")
```

## Expected Output
When conflicts exist, you should see GitError objects with:
- type: 'MERGE_CONFLICT'
- severity: 'error' 
- file: path to conflicted file
- line: line number of conflict marker
- message: description of the conflict marker found

## Conflict Markers Detected
- `<<<<<<< branch_name` - Start of conflict
- `=======` - Separator between versions
- `>>>>>>> branch_name` - End of conflict
