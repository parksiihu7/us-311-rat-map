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
    pg.on("pageerror", lambda e: print("pageerror:", e))
    dls=[]
    pg.on("download", lambda d: dls.append(d))
    pg.goto(f"http://127.0.0.1:{port}/index.html?{sel}",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_timeout(2500)
    pg.click("#btn-csv")
    saved=0
    for round_ in range(20):
        pg.wait_for_timeout(2500)
        label=pg.eval_on_selector("#btn-csv","e=>e.textContent")
        note=pg.eval_on_selector("#export-note","e=>e.textContent")
        print(f"[{round_}] {note} | {label} | downloads={len(dls)}")
        while saved < len(dls):
            try:
                path=f"/workspace/downloads/auto-{saved}.csv"; dls[saved].save_as(path)
                print("saved", saved, os.path.getsize(path)); saved+=1
            except Exception as e:
                print("save err", saved, e); saved+=1
        if label.startswith("Download CSV"): break
        pg.click("#btn-csv")
    b.close()
srv.shutdown()
