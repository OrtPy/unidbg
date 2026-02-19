#!/usr/bin/env python3
import os
import sys
import glob
import zipfile
import subprocess
from datetime import datetime, timezone

def run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
    except Exception as e:
        return f"<failed: {cmd!r} ({e})>"

def main():
    sha = os.environ.get("GITHUB_SHA", "local")
    repo_root = os.getcwd()
    dist_dir = os.path.join(repo_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    jar_paths = sorted(glob.glob("**/target/*.jar", recursive=True))
    jar_paths = [p for p in jar_paths if (os.sep + "target" + os.sep + "original-") not in p]

    out_zip = os.path.join(dist_dir, f"unidbg-build-{sha}.zip")

    info_lines = []
    info_lines.append("unidbg build artifact")
    info_lines.append(f"sha: {sha}")
    info_lines.append(f"utc: {datetime.now(timezone.utc).isoformat()}")
    info_lines.append("")
    info_lines.append(f"java: {run(['java','-version'])}")
    info_lines.append(f"mvnw: {run(['./mvnw','-v'])}")
    info_lines.append("")
    info_lines.append(f"jar_count: {len(jar_paths)}")
    info_lines.append("")

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("build-info.txt", "\n".join(info_lines))
        if not jar_paths:
            zf.writestr("EMPTY.txt", "No jars were found under **/target/*.jar. Did the Maven build succeed?")
        else:
            for p in jar_paths:
                zf.write(p, arcname=p.replace(os.sep, "/"))

    print(f"Created: {out_zip}")
    print(f"Included jars: {len(jar_paths)}")

if __name__ == "__main__":
    sys.exit(main())
