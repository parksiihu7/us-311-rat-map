import functools, http.server, os, threading
from playwright.sync_api import sync_playwright
ROOT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"site")
CHROME=os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a,**k): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Q,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
port=srv.server_address[1]
sel=os.environ.get("SEL","c=cambridge")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1200,"height":800},accept_downloads=True)
    pg.on("console", lambda m: print("console:",m.type,m.text[:200]))
    pg.goto(f"http://127.0.0.1:{port}/index.html?{sel}&f=2012-01-01&t=2026-11-27",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_timeout(3000)
    print("total:",pg.eval_on_selector("#stat-total","e=>e.textContent"))
    try:
        with pg.expect_download(timeout=60000) as dl:
            pg.click("#btn-csv")
        dl.value.save_as("/workspace/downloads/mid-auto.csv"); print("auto saved", os.path.getsize("/workspace/downloads/mid-auto.csv"))
    except Exception as e: print("auto err", e)
    try:
        with pg.expect_download(timeout=60000) as dl:
            pg.click("#save-fallback a")
        dl.value.save_as("/workspace/downloads/mid-fb.csv"); print("fb saved", os.path.getsize("/workspace/downloads/mid-fb.csv"))
    except Exception as e: print("fb err", e)
    b.close()
srv.shutdown()
