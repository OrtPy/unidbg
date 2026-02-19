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

    # Module jars produced by Maven build
    module_jars = sorted(glob.glob("**/target/*.jar", recursive=True))
    # Keep only runtime jars (exclude sources/javadoc and shade originals)
    module_jars = [
        p for p in module_jars
        if not (p.endswith("-sources.jar") or p.endswith("-javadoc.jar"))
        and (os.sep + "target" + os.sep + "original-") not in p
    ]

    # Runtime deps copied by maven-dependency-plugin
    dep_jars = sorted(glob.glob("dist/deps/*.jar"))

    out_zip = os.path.join(dist_dir, f"unidbg-runtime-{sha}.zip")

    info_lines = []
    info_lines.append("unidbg runtime bundle (module jars + deps)")
    info_lines.append(f"sha: {sha}")
    info_lines.append(f"utc: {datetime.now(timezone.utc).isoformat()}")
    info_lines.append("")
    info_lines.append(f"java: {run(['java','-version'])}")
    info_lines.append(f"mvnw: {run(['./mvnw','-v'])}")
    info_lines.append("")
    info_lines.append(f"module_jars: {len(module_jars)}")
    info_lines.append(f"dep_jars: {len(dep_jars)}")
    info_lines.append("")

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("build-info.txt", "\n".join(info_lines))

        # Small helper scripts for Linux/macOS/Windows users
        zf.writestr("run_classpath.sh", "#!/usr/bin/env bash\nCP='lib/*:deps/*'\necho $CP\n")
        zf.writestr("run_classpath.ps1", "$cp='lib/*;deps/*'\nWrite-Output $cp\n")

        if not module_jars and not dep_jars:
            zf.writestr("EMPTY.txt", "No jars found. Did the Maven build succeed?")
        else:
            for p in module_jars:
                zf.write(p, arcname=("lib/" + os.path.basename(p)))
            for p in dep_jars:
                zf.write(p, arcname=("deps/" + os.path.basename(p)))

    print(f"Created: {out_zip}")
    print(f"Module jars: {len(module_jars)}")
    print(f"Dep jars: {len(dep_jars)}")

if __name__ == "__main__":
    sys.exit(main())
