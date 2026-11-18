"""Freeze the shared code before a render fan-out, and check it on every render machine.

    python codeversion.py freeze <label> <file> [<file> ...] > CODE_VERSION.txt
    python codeversion.py check CODE_VERSION.txt      # exit 1 if any file changed since the freeze

Why: many machines import the same kit. If anyone edits a shared .py while renders run, half the
squares come from one version and half from another, and nobody can tell which. Freeze, render,
collect the flags, fix centrally, bump the label (fix1 -> fix2 -> fix3), re-render what changed."""
import sys, hashlib, datetime


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "freeze":
        label, files = sys.argv[2], sys.argv[3:]
        print(f"{label} {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC (frozen; do not edit these files on a render job)")
        for f in files:
            print(md5(f), f)
    elif cmd == "check":
        lines = open(sys.argv[2]).read().splitlines()
        bad = 0
        for ln in lines[1:]:
            if not ln.strip(): continue
            h, f = ln.split(" ", 1)
            try:
                now = md5(f)
            except FileNotFoundError:
                now = "missing"
            if now != h:
                print("CHANGED", f); bad += 1
        print(lines[0].split(" ")[0], "ok" if not bad else f"{bad} file(s) changed: any square rendered now is stale")
        sys.exit(1 if bad else 0)
    else:
        print(__doc__); sys.exit(2)
