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
    pg.on("pageerror", lambda e: print("pageerror:",e))
    pg.on("console", lambda m: print("console:",m.type,m.text) if m.type in ("error","warning") else None)
    pg.goto(f"http://127.0.0.1:{port}/index.html?c=cambridge&f=2012-01-01&t=2026-11-27",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_timeout(4000)
    print("total:",pg.eval_on_selector("#stat-total","e=>e.textContent"))
    with pg.expect_download(timeout=60000) as dl:
        pg.click("#btn-csv")
    path="/workspace/downloads/e2e-small.csv"
    dl.value.save_as(path)
    print("saved",os.path.getsize(path))
    print(open(path).readline().strip())
    b.close()
srv.shutdown()
