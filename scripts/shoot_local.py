import functools
import http.server
import os
import socket
import sys
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    handler = functools.partial(Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/workspace/downloads/poidh-1570-rat-map.png"
    query = sys.argv[2] if len(sys.argv) > 2 else ""
    target = sys.argv[3] if len(sys.argv) > 3 else "local"
    if target.startswith("http"):
        srv, port = None, None
        url = target + query
    else:
        srv, port = serve()
        url = f"http://127.0.0.1:{port}/index.html{query}"
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome"), args=["--no-sandbox","--force-device-scale-factor=1"])
        page = browser.new_page(viewport={"width": 1440, "height": int(os.environ.get("VH", "900"))}, device_scale_factor=1)
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_function("window.__atlasReady === true", timeout=60000)
        # wait until the load bar is gone and a real total is rendered
        page.wait_for_function(
            "() => { const e=document.getElementById('stat-total'); return e && parseInt(e.textContent.replace(/,/g,'')) > 1000; }",
            timeout=180000,
        )
        page.wait_for_function("() => !document.getElementById('loadbar').classList.contains('show')", timeout=240000)
        page.wait_for_timeout(3000)
        total = page.eval_on_selector("#stat-total", "e => e.textContent")
        print("stat-total:", total)
        print("badge:", page.eval_on_selector("#top-badge", "e => e.textContent"))
        page.screenshot(path=out, full_page=False)
        print("saved", out)
        for e in errors[:20]:
            print("console:", e)
        browser.close()
    if srv: srv.shutdown()


if __name__ == "__main__":
    main()
