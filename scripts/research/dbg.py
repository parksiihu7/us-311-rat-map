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
    pg=b.new_page(viewport={"width":1200,"height":800})
    pg.on("console", lambda m: print("console:",m.type,m.text[:200]))
    pg.on("pageerror", lambda e: print("pageerror:",e))
    pg.goto(f"http://127.0.0.1:{port}/index.html?f=2012-01-01&t=2026-11-27",wait_until="domcontentloaded")
    pg.wait_for_function("window.__atlasReady===true",timeout=60000)
    pg.wait_for_function("() => !document.getElementById('loadbar').classList.contains('show')",timeout=240000)
    pg.wait_for_timeout(2000)
    print(pg.evaluate("""() => {
      const S=window.__S;
      const sf=Object.fromEntries([...S.chunks.entries()].filter(([k])=>k.startsWith('san')));
      const sfN=Object.values(sf).map(c=>c.n);
      const cc=[...(S.lastMeta.cityCounts||new Map()).entries()];
      return {sfN, sfSum: sfN.reduce((a,b)=>a+b,0), cityCounts: cc,
              metaTotal: S.lastMeta.total};
    }"""))
    b.close()
srv.shutdown()
