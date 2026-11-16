import py_compile
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

files = [
    'app.py',
    'models.py',
    'config.py',
    'utils.py',
    'routes/auth.py',
    'routes/student.py',
    'routes/admin.py',
    'routes/found.py',
    'routes/lost.py',
    'routes/matches.py',
    'routes/requests.py',
    'routes/notifications.py',
    'ai_engine/matching.py',
    'ai_engine/preprocessing.py',
]

errors = []
for f in files:
    if not os.path.exists(f):
        print(f"  SKIP  {f} (not found)")
        continue
    try:
        py_compile.compile(f, doraise=True)
        print(f"  OK    {f}")
    except py_compile.PyCompileError as e:
        print(f"  ERROR {f}: {e}")
        errors.append(f)

print()
if errors:
    print(f"FAILED: {len(errors)} file(s) have syntax errors.")
    sys.exit(1)
else:
    print("All files passed syntax check.")
