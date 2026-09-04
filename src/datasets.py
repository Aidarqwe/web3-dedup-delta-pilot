import os
import sys
import json
import shutil
import subprocess
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))

# Both sources are pinned to a fixed date so the datasets are reproducible
CUTOFF = "2026-08-30T00:00:00Z"

GIT_URL = "https://github.com/pallets/click.git"
GIT_SUBDIR = "src"
GIT_NVERSIONS = 20
GIT_EXTS = (".py", ".rst", ".txt", ".cfg", ".toml", ".ini", ".md")

WIKI_TITLE = "Content-addressable_storage"
WIKI_NREVS = 20

RANDOM_NVERS = 10
RANDOM_SIZE = 64 * 1024


def _save(name, versions):
    d = os.path.join(DATA, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    for i, v in enumerate(versions, 1):
        with open(os.path.join(d, f"v{i:03d}.bin"), "wb") as f:
            f.write(v)
    total = sum(len(v) for v in versions)
    print(f"  {name:12s}: {len(versions):3d} versions, {total/1024:9.1f} KiB "
          f"({total/len(versions)/1024:.1f} KiB/version)")


def build_git_repo():
    work = os.path.join(DATA, "_gitwork")
    shutil.rmtree(work, ignore_errors=True)
    print(f"  cloning {GIT_URL}")
    subprocess.run(["git", "clone", "--quiet", GIT_URL, work], check=True)

    log = subprocess.run(
        ["git", "-C", work, "log", f"--before={CUTOFF}", "--format=%H",
         "-n", str(GIT_NVERSIONS), "--", GIT_SUBDIR],
        capture_output=True, text=True, check=True).stdout.split()
    commits = list(reversed(log))                     # oldest first

    versions = []
    for c in commits:
        subprocess.run(["git", "-C", work, "checkout", "--quiet", c], check=True)
        blob = bytearray()
        for dirpath, _, names in sorted(os.walk(os.path.join(work, GIT_SUBDIR))):
            for n in sorted(names):
                if n.endswith(GIT_EXTS):
                    p = os.path.join(dirpath, n)
                    blob += f"\n===== {os.path.relpath(p, work)} =====\n".encode()
                    blob += open(p, "rb").read()
        versions.append(bytes(blob))
    shutil.rmtree(work, ignore_errors=True)
    _save("git_repo", versions)


def build_wiki():
    api = ("https://en.wikipedia.org/w/api.php?action=query&prop=revisions"
           f"&titles={WIKI_TITLE}&rvlimit={WIKI_NREVS}&rvstart={CUTOFF}&rvdir=older"
           "&rvprop=content|ids|timestamp&rvslots=main&format=json&formatversion=2")
    req = urllib.request.Request(api, headers={"User-Agent": "thesis-pilot/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        revs = json.load(r)["query"]["pages"][0]["revisions"]
    versions = [rv["slots"]["main"]["content"].encode("utf-8") for rv in reversed(revs)]
    _save("wiki", versions)


def build_random():
    _save("random_bin", [os.urandom(RANDOM_SIZE) for _ in range(RANDOM_NVERS)])


def main():
    os.makedirs(DATA, exist_ok=True)
    which = sys.argv[1:] or ["git", "wiki", "random"]
    print(f"building {which} -> {DATA}")
    if "git" in which:
        build_git_repo()
    if "wiki" in which:
        build_wiki()
    if "random" in which:
        build_random()


if __name__ == "__main__":
    main()
