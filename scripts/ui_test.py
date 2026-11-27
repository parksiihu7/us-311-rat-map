import functools, http.server, os, threading
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME=os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a,**k): pass
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Q,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
port=srv.server_address[1]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1440,"height":900},accept_downloads=True)
    errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"http://127.0.0.1:{port}/index.html",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_function("() => !document.getElementById('loadbar').classList.contains('show')",timeout=180000)
    pg.wait_for_timeout(1000)
    print("default total:", pg.eval_on_selector("#stat-total","e=>e.textContent"))
    # toggle chicago off
    pg.click(".city-row input[data-slug='chicago']")
    pg.wait_for_timeout(2500)
    print("without chicago:", pg.eval_on_selector("#stat-total","e=>e.textContent"))
    # all years
    pg.click("#range-presets button[data-range='all']")
    pg.wait_for_function("() => !document.getElementById('loadbar').classList.contains('show')",timeout=240000)
    pg.wait_for_timeout(1500)
    print("all years, no chicago:", pg.eval_on_selector("#stat-total","e=>e.textContent"))
    # back to all cities + all years
    pg.click("#city-presets button[data-cities='all']")
    pg.wait_for_function("() => !document.getElementById('loadbar').classList.contains('show')",timeout=240000)
    pg.wait_for_timeout(1500)
    print("all cities all years:", pg.eval_on_selector("#stat-total","e=>e.textContent"))
    # popup click on Chicago
    pt=pg.evaluate("""() => { const m=window.__map; const p=m.latLngToContainerPoint([41.8781,-87.6298]); const r=document.getElementById('map').getBoundingClientRect(); return {x:r.x+p.x, y:r.y+p.y}; }""")
    pg.mouse.click(pt["x"], pt["y"])
    pg.wait_for_timeout(800)
    print("popup:", pg.eval_on_selector_all(".leaflet-popup-content","els=>els.map(e=>e.textContent.slice(0,80))"))
    print("errors:", errs[:5])
    b.close()
srv.shutdown()
