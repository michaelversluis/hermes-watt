"""Invoke Hermes' unmodified official catalog validator."""
import json
import sys
from pathlib import Path
from hermes_cli.plugin_validate import validate_plugin_dir
report=validate_plugin_dir(Path(sys.argv[1]).resolve())
print(json.dumps(report.to_dict(),indent=2))
raise SystemExit(report.exit_code)
