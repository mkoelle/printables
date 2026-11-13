#!/usr/bin/env python3
"""Run a project script inside the open FreeCAD, through the FreeCAD MCP
addon's RPC server (127.0.0.1:9875). Used by the mise tasks.

  python3 tools/fc.py tophat/models/hat.py
  python3 tools/fc.py tophat/models/tests.py TEST_GROUPS=fit,rail
  python3 tools/fc.py --status

NAME=VALUE arguments become globals of the script, each value a list split
on commas. The script runs in a fresh namespace with __file__ set, so it
finds its project from its own path.

FreeCAD runs one script at a time, so calls take a lock first: a second
build waits for the first instead of colliding with it. Exits non-zero when
the script raises, a check fails ("CHECK(S) FAILED") or FreeCAD is not
reachable.
"""
import fcntl
import os
import sys
import time
import xmlrpc.client
from pathlib import Path

URL = "http://127.0.0.1:9875"  # not localhost: it can resolve to ::1 and hang
LOCK = Path.home() / ".cache" / "freecad-rpc.lock"
TIMEOUT = 1800  # the addon's ceiling for one execute_code call, in seconds
READY_TIMEOUT = 15
ERROR = "fc.py: SCRIPT ERROR"

RUN = """
def _fc_run():
    import sys, traceback
    path = {path!r}
    try:
        exec(compile(open(path).read(), path, "exec"),
             {{"__file__": path, "__name__": "__main__", **{opts!r}}})
    except BaseException:
        traceback.print_exc(file=sys.stdout)
        print({error!r})
_fc_run()
del _fc_run
"""


def server():
    return xmlrpc.client.ServerProxy(URL, allow_none=True)


def unreachable(e):
    sys.exit(f"fc.py: FreeCAD RPC server not reachable at {URL} ({e}).\n"
             "Open FreeCAD and start the RPC server (MCP Addon workbench).")


def main(args):
    if args == ["--status"]:
        try:
            print(server().get_rpc_status())
        except OSError as e:
            unreachable(e)
        return 0
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    path = Path(args[0]).resolve()
    if not path.is_file():
        sys.exit(f"fc.py: no such script: {path}")
    opts = {}
    for a in args[1:]:
        name, _, value = a.partition("=")
        opts[name] = [v for v in value.split(",") if v]

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("fc.py: waiting for another FreeCAD run to finish...", flush=True)
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            # The script's timeout also bounds its wait in FreeCAD's queue, so
            # first check that FreeCAD takes scripts at all: an open dialog
            # blocks it while the RPC server still reports healthy.
            ready = server().execute_code("pass", READY_TIMEOUT)
            if not ready.get("success"):
                sys.exit(f"fc.py: FreeCAD is not running scripts: {ready.get('error')}\n"
                         "Close any open dialog in FreeCAD and try again.")
            print(f"fc.py: running {os.path.relpath(path)} in FreeCAD", flush=True)
            start = time.time()
            res = server().execute_code(RUN.format(path=str(path), opts=opts, error=ERROR), TIMEOUT)
        except (OSError, xmlrpc.client.Fault) as e:
            unreachable(e)

    out = res.get("message", "").split("Output: ", 1)[-1]
    print(out.rstrip())
    print(f"fc.py: {time.time() - start:.0f} s")
    if not res.get("success"):
        print(f"fc.py: FreeCAD error: {res.get('error')}")
        return 1
    return 1 if ERROR in out or "CHECK(S) FAILED" in out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
