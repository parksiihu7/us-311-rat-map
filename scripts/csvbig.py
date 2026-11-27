import functools, http.server, os, threading, time
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
    pg.on("console", lambda m: print("console:",m.type,m.text[:200]) if m.type=="error" else None)
    got=[]
    pg.on("download", lambda d: got.append(d))
    pg.goto(f"http://127.0.0.1:{port}/index.html?c=chicago&f=2012-01-01&t=2026-11-27",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_function("() => { const e=document.getElementById('stat-total'); return e && parseInt(e.textContent.replace(/,/g,'')) > 600000; }",timeout=300000)
    print("total:",pg.eval_on_selector("#stat-total","e=>e.textContent"))
    t=time.time()
    pg.click("#btn-csv")
    # wait for note to report completion
    pg.wait_for_function("() => document.getElementById('export-note').textContent.includes('Downloaded')", timeout=600000)
    print("note:",pg.eval_on_selector("#export-note","e=>e.textContent"), f"{time.time()-t:.0f}s")
    print("auto downloads:", len(got))
    try:
        print("page alive:", pg.evaluate("1+1"))
        print("fallback html:", pg.eval_on_selector("#save-fallback","e=>e.innerHTML.slice(0,200)"))
    except Exception as e:
        print("page dead:", e)
    try:
        with pg.expect_download(timeout=120000) as dl:
            pg.click("#save-fallback a")
        p2="/workspace/downloads/e2e-big-fallback.csv"
        dl.value.save_as(p2)
        print("fallback saved", os.path.getsize(p2))
    except Exception as e:
        print("fallback err:", e)

    b.close()
srv.shutdown()
