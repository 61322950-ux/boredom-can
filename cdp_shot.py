#!/usr/bin/env python3
"""用 Chrome DevTools Protocol 精确控制视口渲染截图（与真机一致的设备模拟）"""
import base64, json, subprocess, time, urllib.request, sys, os
import websocket

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9223
OUT = "/Users/wangkun/Desktop/untitled folder 3/无聊罐头/验收截图"
BASE = ("file:///Users/wangkun/Desktop/untitled%20folder%203/"
        "%E6%97%A0%E8%81%8A%E7%BD%90%E5%A4%B4/%E6%97%A0%E8%81%8A%E7%BD%90%E5%A4%B4.html")
W, H, DPR = 420, 860, 2

class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=15)
        self.mid = 0
    def cmd(self, method, **params):
        self.mid += 1
        self.ws.send(json.dumps({"id": self.mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

proc = subprocess.Popen([
    CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
    f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
    "--user-data-dir=/tmp/bc-chrome-profile",
    "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    target = None
    for _ in range(40):
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
            pages = [t for t in tabs if t.get("type") == "page"]
            if pages:
                target = pages[0]
                break
        except Exception:
            pass
        time.sleep(0.25)
    if not target:
        raise RuntimeError("无法连接 Chrome 调试端口")

    cdp = CDP(target["webSocketDebuggerUrl"])
    cdp.cmd("Emulation.setDeviceMetricsOverride",
            width=W, height=H, deviceScaleFactor=DPR, mobile=True)
    cdp.cmd("Page.enable")

    shots = [
        ("hero",      f"{BASE}"),
        ("woodfish",  f"{BASE}?only=woodfish&shot=1"),
        ("bubble",    f"{BASE}?only=bubble&shot=1"),
        ("stone",     f"{BASE}?only=stone&shot=1"),
        ("rain",      f"{BASE}?only=rain&shot=1"),
        ("poke",      f"{BASE}?only=poke&shot=1"),
        ("noodle",    f"{BASE}?only=noodle&shot=1"),
        ("kiddy",     f"{BASE}?only=kiddy&shot=1"),
        ("brush",     f"{BASE}?only=brush&shot=1"),
        ("radio",     f"{BASE}?only=radio&shot=1"),
        ("trophy",    f"{BASE}?only=trophy&shot=1"),
        ("dark-kiddy",f"{BASE}?theme=dark&only=kiddy&shot=1"),
    ]
    for name, url in shots:
        cdp.cmd("Page.navigate", url=url)
        time.sleep(1.4)  # 等 load + JS 执行（headless file:// 本地秒开）
        data = cdp.cmd("Page.captureScreenshot", format="png")
        with open(os.path.join(OUT, f"{name}.png"), "wb") as f:
            f.write(base64.b64decode(data["data"]))
        print(f"{name}: {os.path.getsize(os.path.join(OUT, name + '.png'))} bytes")
    print("ALL DONE")
finally:
    proc.terminate()
