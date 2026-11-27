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
    pg.wait_for_timeout(3000)
    # A: plain string blob 30MB, click via evaluate
    pg.evaluate("""() => {
      const line='2026-01-01,New York City,NY,40.71234,-74.00567,Rat sighting,Rodent / Rat Sighting,NYC Open Data,erm2-nwe9\\n';
      let s=''; const parts=[];
      for(let i=0;i<350000;i++){ s+=line; if(s.length>2e6){parts.push(s); s='';} }
      if(s)parts.push(s);
      const blob=new Blob(parts,{type:'text/csv'});
      window.__blobA=blob;
      const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='probeA.csv'; a.id='probeA'; a.textContent='A'; document.body.appendChild(a);
      a.click();
    }""")
    print("blobA size:", pg.evaluate("window.__blobA.size"))
    try:
        with pg.expect_download(timeout=30000) as dl:
            pg.click("#probeA")
        dl.value.save_as("/workspace/downloads/probeA.csv"); print("A saved", os.path.getsize("/workspace/downloads/probeA.csv"))
    except Exception as e: print("A err", e)
    # B: same content but Uint8Array parts (TextEncoder), like exportCsv
    pg.evaluate("""() => {
      const line='2026-01-01,New York City,NY,40.71234,-74.00567,Rat sighting,Rodent / Rat Sighting,NYC Open Data,erm2-nwe9\n';
      const enc=new TextEncoder(); const parts=[enc.encode('header\n')]; let buf=[],bytes=0;
      for(let i=0;i<350000;i++){ buf.push(line); bytes+=line.length; if(bytes>4e6){ parts.push(enc.encode(buf.join(''))); buf=[]; bytes=0; } }
      if(buf.length)parts.push(enc.encode(buf.join('')));
      const blob=new Blob(parts,{type:'text/csv'});
      window.__blobB=blob;
      const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='probeB.csv'; a.id='probeB'; a.textContent='B'; document.body.appendChild(a);
      a.click();
    }""")
    print("blobB size:", pg.evaluate("window.__blobB.size"))
    try:
        with pg.expect_download(timeout=30000) as dl:
            pg.click("#probeB")
        dl.value.save_as("/workspace/downloads/probeB.csv"); print("B saved", os.path.getsize("/workspace/downloads/probeB.csv"))
    except Exception as e: print("B err", e)
    b.close()
srv.shutdown()
