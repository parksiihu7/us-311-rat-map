"""End-to-end check of the atlas: full-range load, filters, CSV export, screenshots."""
import functools
import http.server
import os
import sys
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
OUT = "/workspace/downloads"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):
        pass


def serve():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main():
    srv, port = serve()
    base = f"http://127.0.0.1:{port}/index.html"
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type == "error" else None)

        # 1. full history
        t0 = time.time()
        page.goto(base + "?f=2012-01-01&t=2026-11-27", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_function("window.__atlasReady === true", timeout=60000)
        page.wait_for_function(
            "() => { const e=document.getElementById('stat-total'); return e && parseInt(e.textContent.replace(/,/g,'')) > 1000000; }",
            timeout=300000,
        )
        print("full-range total:", page.eval_on_selector("#stat-total", "e => e.textContent"), f"in {time.time()-t0:.0f}s")
        page.wait_for_timeout(4000)
        page.screenshot(path=f"{OUT}/e2e-national.png")

        # 2. city zoom (NYC)
        page.evaluate("window.__map = null")
        page.mouse.move(720, 450)
        page.click("#city-presets button[data-cities='none']")
        page.wait_for_timeout(500)
        page.click(".city-row input[data-slug='nyc']")
        page.wait_for_timeout(2500)
        print("NYC only:", page.eval_on_selector("#stat-total", "e => e.textContent"))

        # 3. CSV export of a small selection
        page.click("#city-presets button[data-cities='big']")
        page.wait_for_timeout(1500)
        with page.expect_download(timeout=180000) as dl:
            page.click("#btn-csv")
        d = dl.value
        path = f"{OUT}/e2e-export.csv"
        d.save_as(path)
        size = os.path.getsize(path)
        with open(path) as f:
            head = f.readline().strip()
            n = sum(1 for _ in f)
        print("csv:", path, f"{size/1e6:.1f} MB", n, "rows")
        print("header:", head)

        # 4. methodology modal
        page.click("#btn-method")
        page.wait_for_timeout(800)
        page.screenshot(path=f"{OUT}/e2e-method.png")
        print("modal visible:", page.is_visible("#modal.show"))

        for e in errors[:10]:
            print("console:", e)
        browser.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
