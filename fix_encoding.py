"""
fix_encoding.py — Adds UTF-8 stdout reconfiguration to all Python backend files
"""
import sys
import os

FIX_LINE = "import sys; sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"

files = [
    r"C:\Users\ASUS\Downloads\Shipping\backend\model_trainer.py",
    r"C:\Users\ASUS\Downloads\Shipping\backend\app.py",
    r"C:\Users\ASUS\Downloads\Shipping\backend\report_generator.py",
    r"C:\Users\ASUS\Downloads\Shipping\backend\data_processor.py",
    r"C:\Users\ASUS\Downloads\Shipping\run.py",
    r"C:\Users\ASUS\Downloads\Shipping\test_pipeline.py",
]

for path in files:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if FIX_LINE.strip() in content:
        print(f"Already fixed: {path}")
        continue
    # Insert after the first docstring / import or at beginning
    lines = content.split('\n')
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith('"""') or line.startswith("'"):
            # Find end of docstring
            if i > 0:
                for j in range(i+1, len(lines)):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        insert_at = j + 1
                        break
                break
        elif line.startswith('import') or line.startswith('from'):
            insert_at = i
            break
    lines.insert(insert_at, FIX_LINE.strip())
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Fixed: {path}")

print("Done!")
