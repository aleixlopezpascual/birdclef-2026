#!/usr/bin/env python3
"""
Execute code in a running Jupyter kernel via REST API.
Usage:
    python scripts/jupyter_exec.py "print('hello')"
    python scripts/jupyter_exec.py --file scripts/debug_training.py

Requires: pip install requests websocket-client
Assumes Jupyter is tunneled to localhost:8080 (via gmlp notebook connect).
"""
import argparse
import json
import sys
import time
import uuid

try:
    import requests
    import websocket
except ImportError:
    print("Install: pip install requests websocket-client")
    sys.exit(1)

BASE = "http://localhost:8080"
WS_BASE = "ws://localhost:8080"


def get_or_create_kernel(token=None):
    headers = {"Authorization": f"token {token}"} if token else {}
    r = requests.get(f"{BASE}/api/kernels", headers=headers)
    r.raise_for_status()
    kernels = r.json()
    if kernels:
        kid = kernels[0]["id"]
        print(f"[jupyter_exec] Using existing kernel: {kid}")
        return kid
    # Start a new python3 kernel
    r = requests.post(f"{BASE}/api/kernels", json={"name": "python3"}, headers=headers)
    r.raise_for_status()
    kid = r.json()["id"]
    print(f"[jupyter_exec] Started new kernel: {kid}")
    time.sleep(3)
    return kid


def execute(code, token=None, timeout=300):
    headers = {"Authorization": f"token {token}"} if token else {}
    kid = get_or_create_kernel(token)
    ws_url = f"{WS_BASE}/api/kernels/{kid}/channels"
    if token:
        ws_url += f"?token={token}"

    msg_id = str(uuid.uuid4())
    execute_msg = {
        "header": {
            "msg_id": msg_id,
            "username": "copilot",
            "session": str(uuid.uuid4()),
            "msg_type": "execute_request",
            "version": "5.3",
        },
        "parent_header": {},
        "metadata": {},
        "content": {
            "code": code,
            "silent": False,
            "store_history": True,
            "user_expressions": {},
            "allow_stdin": False,
        },
        "channel": "shell",
        "buffers": [],
    }

    outputs = []
    ws = websocket.create_connection(ws_url, timeout=timeout)
    ws.send(json.dumps(execute_msg))

    deadline = time.time() + timeout
    while time.time() < deadline:
        raw = ws.recv()
        msg = json.loads(raw)
        mtype = msg.get("msg_type", "")
        parent_id = msg.get("parent_header", {}).get("msg_id", "")
        if parent_id != msg_id:
            continue
        if mtype == "stream":
            text = msg["content"].get("text", "")
            print(text, end="")
            outputs.append(text)
        elif mtype == "execute_result":
            text = msg["content"]["data"].get("text/plain", "")
            print(text)
            outputs.append(text)
        elif mtype == "error":
            err = "\n".join(msg["content"].get("traceback", []))
            print(f"ERROR:\n{err}", file=sys.stderr)
            outputs.append(f"ERROR: {err}")
            break
        elif mtype == "execute_reply":
            break
    ws.close()
    return "".join(outputs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("code", nargs="?", help="Python code to execute")
    parser.add_argument("--file", "-f", help="Python file to execute")
    parser.add_argument("--token", "-t", default=None, help="Jupyter token (if required)")
    parser.add_argument("--port", "-p", default=8080, type=int)
    args = parser.parse_args()

    if args.port != 8080:
        BASE = f"http://localhost:{args.port}"
        WS_BASE = f"ws://localhost:{args.port}"

    if args.file:
        with open(args.file) as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        code = sys.stdin.read()

    execute(code, token=args.token)
