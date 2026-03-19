from pathlib import Path
from econflow.core import find_workspace
from econflow.webui import _workspace_projects, _stage_sections

root = find_workspace()
print('Testing _workspace_projects...')
try:
    projects = _workspace_projects(root)
    print(f'✓ _workspace_projects OK ({len(projects)} projects)')
    for p in projects:
        print(f'  - {p.get("slug")}: {p.get("title")}')
except Exception as e:
    import traceback
    print(f'✗ ERROR:')
    traceback.print_exc()

print()
print('Testing _stage_sections...')
try:
    stages = _stage_sections(root)
    print(f'✓ _stage_sections OK ({len(stages)} stages)')
except Exception as e:
    import traceback
    print(f'✗ ERROR:')
    traceback.print_exc()
