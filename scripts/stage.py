"""Stage only distributable sources; never developer environments or local receipts."""
from pathlib import Path
import shutil

def stage(destination):
    root=Path(__file__).resolve().parents[1]
    dest=Path(destination)
    dest.mkdir(parents=True,exist_ok=True)
    for name in ["__init__.py","plugin.yaml","README.md","LICENSE","dashboard","desktop"]:
        source=root/name
        if not source.exists(): continue
        if source.is_dir():
            shutil.copytree(source,dest/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
        else: shutil.copy2(source,dest/name)
    return dest

if __name__=="__main__":
    import sys
    print(stage(sys.argv[1]))
