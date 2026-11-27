import functools, http.server, os, threading
from playwright.sync_api import sync_playwright
ROOT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"site")
CHROME=os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a,**k): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Q,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
port=srv.server_address[1]
sel=os.environ.get("SEL","c=nyc&f=2012-01-01&t=2026-11-27")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1200,"height":800},accept_downloads=True)
    pg.evaluate  # noop
    pg.on("pageerror", lambda e: print("pageerror:", e))
    pg.goto(f"http://127.0.0.1:{port}/index.html?{sel}",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_timeout(2500)
    pg.evaluate("window.__noAutoDl = true")   # we click the save links ourselves
    part=0
    pg.click("#btn-csv")
    while True:
        pg.wait_for_timeout(1500)
        note=pg.eval_on_selector("#export-note","e=>e.textContent")
        label=pg.eval_on_selector("#btn-csv","e=>e.textContent")
        print("note:",note,"| button:",label)
        # save via link (a real click)
        try:
            with pg.expect_download(timeout=30000) as dl:
                pg.click("#dl-this")
            path=f"/workspace/downloads/job-{part}.csv"; dl.value.save_as(path)
            print("saved part",part,os.path.getsize(path)); part+=1
        except Exception as e:
            print("save err", e)
        if label.startswith("Download CSV"):
            break
        pg.click("#btn-csv")
        if part>20: break
    b.close()
srv.shutdown()
