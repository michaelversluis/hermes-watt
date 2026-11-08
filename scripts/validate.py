"""Run the documented Hermes CLI validator (no private core imports)."""
import argparse
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("package", type=Path)
parser.add_argument("--hermes", default="hermes", help="Path to the official Hermes CLI executable")
args = parser.parse_args()
raise SystemExit(subprocess.run([args.hermes, "plugins", "validate", str(args.package.resolve()), "--install-deps"]).returncode)
