"""Build the kubectl plugin archive for Krew from a built incident2chaos wheel.

The archive holds one file, kubectl-incident2chaos: a Python zip application that
carries incident2chaos and the pure-Python part of PyYAML, so it needs only Python 3.9
or later on the PATH as python3 (Linux and macOS). It also holds the license files.

Usage: python build_plugin.py --wheel dist/incident2chaos-X.Y.Z-py3-none-any.whl
                              --source . --out plugin/
"""

import argparse
import glob
import gzip
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipapp
from pathlib import Path

PYYAML = "PyYAML==6.0.3"   # pinned; its C extension is removed, the pure-Python loader stays
NAME = "kubectl-incident2chaos"
EPOCH = 315532800          # Jan 1, 1980 UTC: the earliest time a zip entry can carry

# Runs first inside the zip application: shows "kubectl incident2chaos" in usage text
# when kubectl starts it as a plugin, then hands over to the tool's own entry point.
MAIN = '''import argparse
import os
import sys

if os.path.basename(sys.argv[0]).startswith("kubectl-"):
    _init = argparse.ArgumentParser.__init__

    def _init_as_plugin(self, *args, **kwargs):
        if kwargs.get("prog") == "incident2chaos":
            kwargs["prog"] = "kubectl incident2chaos"
        _init(self, *args, **kwargs)

    argparse.ArgumentParser.__init__ = _init_as_plugin

from incident2chaos.cli import main

sys.exit(main())
'''


def pip_target(target, *requirements):
    """Install requirements into target with no dependencies and no compiled caches."""
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--no-deps", "--no-compile",
                    "--target", str(target), *requirements], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wheel", required=True, help="the incident2chaos wheel to package")
    parser.add_argument("--source", required=True, help="the repository at the release tag (license files)")
    parser.add_argument("--out", required=True, help="folder for the archive")
    args = parser.parse_args(argv)
    os.environ["TZ"] = "UTC"     # zip entries store local time: build in UTC so every machine gives the same bytes
    if hasattr(time, "tzset"):
        time.tzset()

    wheel = glob.glob(args.wheel)
    if len(wheel) != 1:
        parser.error(f"--wheel must match exactly one file, matched {len(wheel)}")
    source, out = Path(args.source), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        app, meta, stage = Path(tmp, "app"), Path(tmp, "meta"), Path(tmp, "stage")
        pip_target(app, wheel[0])
        pip_target(meta, PYYAML)
        shutil.copytree(meta / "yaml", app / "yaml",
                        ignore=shutil.ignore_patterns("*.so", "*.pyd", "__pycache__"))
        pyyaml_license = next(meta.glob("[Pp]y[Yy][Aa][Mm][Ll]-*.dist-info/licenses/LICENSE"), None) \
            or next(meta.glob("[Pp]y[Yy][Aa][Mm][Ll]-*.dist-info/LICENSE"))
        for item in app.iterdir():
            if item.name.endswith(".dist-info") or item.name == "bin" or item.name == "__pycache__":
                shutil.rmtree(item)
        (app / "__main__.py").write_text(MAIN, encoding="utf-8")

        for path in [app, *app.rglob("*")]:
            os.utime(path, (EPOCH, EPOCH))
        stage.mkdir()
        target = stage / NAME
        zipapp.create_archive(app, target, interpreter="/usr/bin/env python3", compressed=True,
                              filter=lambda p: "__pycache__" not in p.parts)
        target.chmod(0o755)
        shutil.copy(source / "LICENSE", stage / "LICENSE")
        shutil.copy(source / "NOTICE", stage / "NOTICE")
        shutil.copy(source / "data" / "LICENSE", stage / "LICENSE-data")
        shutil.copy(pyyaml_license, stage / "LICENSE-PyYAML")

        archive = out / f"{NAME}.tar.gz"
        with open(archive, "wb") as raw, \
                gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=EPOCH) as packed, \
                tarfile.open(fileobj=packed, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for name in [NAME, "LICENSE", "NOTICE", "LICENSE-data", "LICENSE-PyYAML"]:
                info = tar.gettarinfo(stage / name, arcname=name)
                info.mtime, info.uid, info.gid, info.uname, info.gname = EPOCH, 0, 0, "", ""
                info.mode = 0o755 if name == NAME else 0o644
                with open(stage / name, "rb") as handle:
                    tar.addfile(info, handle)
    print(archive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
