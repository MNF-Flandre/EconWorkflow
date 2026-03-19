from pathlib import Path
from econflow.core import find_workspace, load_config, load_role_specs
from econflow.processes import default_process_id
from econflow.webui import _load_secrets, PIPELINES, PIPELINE_LABELS

root = find_workspace()
print("=" * 50)
print("Testing inject_globals components...")
print("=" * 50)

try:
    config = load_config(root)
    print(f"✓ load_config OK")
except Exception as e:
    print(f"✗ load_config ERROR: {e}")

try:
    secrets = _load_secrets(root)
    print(f"✓ _load_secrets OK")
except Exception as e:
    print(f"✗ _load_secrets ERROR: {e}") 

try:
    role_specs = load_role_specs(root)
    print(f"✓ load_role_specs OK ({len(role_specs)} roles)")
    # Print first role to check structure
    for role_id, spec in list(role_specs.items())[:3]:
        print(f"  - {role_id}: {spec}")
except Exception as e:
    import traceback
    print(f"✗ load_role_specs ERROR: {e}")
    traceback.print_exc()

try:
    process_id = default_process_id(root)
    print(f"✓ default_process_id OK: {process_id}")
except Exception as e:
    print(f"✗ default_process_id ERROR: {e}")

print("\nPIPELINES:", len(PIPELINES), "pipelines")
for k, v in PIPELINES.items():
    print(f"  - {k}: {len(v)} roles")

print("\nPIPELINE_LABELS:", PIPELINE_LABELS.keys())
