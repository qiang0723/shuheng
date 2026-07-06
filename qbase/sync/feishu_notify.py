#!/usr/bin/env python3
"""飞书自定义机器人告警(带签名校验)。秘钥读 /etc/shuheng/sentinel.env,不入 git。
用法: feishu_notify.py "<text>"   (或从 stdin 读)"""
import sys, os, time, json, hmac, hashlib, base64, urllib.request

ENVF = os.environ.get("SENTINEL_ENV", "/etc/shuheng/sentinel.env")

def load_env(p):
    d = {}
    with open(p) as f:
        for ln in f:
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                d[k.strip()] = v.strip()
    return d

def main():
    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    e = load_env(ENVF)
    hook, secret = e["FEISHU_WEBHOOK"], e.get("FEISHU_SIGN_SECRET", "")
    payload = {"msg_type": "text", "content": {"text": text}}
    if secret:
        ts = str(int(time.time()))
        sign = base64.b64encode(
            hmac.new(f"{ts}\n{secret}".encode(), digestmod=hashlib.sha256).digest()
        ).decode()
        payload["timestamp"], payload["sign"] = ts, sign
    req = urllib.request.Request(
        hook, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    print(urllib.request.urlopen(req, timeout=15).read().decode())

if __name__ == "__main__":
    main()
