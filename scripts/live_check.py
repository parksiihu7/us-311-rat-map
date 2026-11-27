"""Final live verification: load the published site, check counts, export a small CSV."""
import os
from playwright.sync_api import sync_playwright
CHROME=os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1440,"height":900},accept_downloads=True)
    errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto("https://parksiihu7.github.io/us-311-rat-map/?c=cambridge&f=2012-01-01&t=2026-11-27", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_function("window.__atlasReady===true",timeout=90000)
    pg.wait_for_function("() => !document.getElementById('loadbar').classList.contains('show')",timeout=240000)
    pg.wait_for_timeout(1500)
    print("total(cambridge):", pg.eval_on_selector("#stat-total","e=>e.textContent"))
    with pg.expect_download(timeout=120000) as dl:
        pg.click("#btn-csv")
    path="/workspace/downloads/live-export.csv"; dl.value.save_as(path)
    print("csv bytes:", os.path.getsize(path))
    print("csv header:", open(path).readline().strip())
    print("errors:", errs[:5])
    b.close()
