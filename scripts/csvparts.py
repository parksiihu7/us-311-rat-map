import functools, http.server, os, threading
from playwright.sync_api import sync_playwright
ROOT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"site")
CHROME=os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a,**k): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Q,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
port=srv.server_address[1]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1200,"height":800},accept_downloads=True)
    pg.goto(f"http://127.0.0.1:{port}/index.html?c=nyc&f=2012-01-01&t=2026-11-27",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_timeout(2500)
    pg.evaluate("window.__noAutoDl = true")
    pg.click("#btn-csv")
    pg.wait_for_function("() => document.getElementById('export-note').textContent.includes('Downloaded')", timeout=180000)
    print("note:", pg.eval_on_selector("#export-note","e=>e.textContent"))
    n=pg.eval_on_selector_all("#save-fallback a","els=>els.length")
    print("links:", n)
    for i in range(n):
        try:
            with pg.expect_download(timeout=60000) as dl:
                pg.click(f"#save-fallback a:nth-of-type({i+1})")
            path=f"/workspace/downloads/part-{i}.csv"; dl.value.save_as(path)
            print("saved", i, os.path.getsize(path))
        except Exception as e:
            print("err", i, e)
    b.close()
srv.shutdown()
