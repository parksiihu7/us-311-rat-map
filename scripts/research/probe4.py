import json, urllib.parse, urllib.request
def get(url, timeout=50, raw=False):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b=r.read()
            return json.loads(b) if not raw else b[:300]
    except Exception as e: return {"__err":str(e)}

for host,q in [("data.seattle.gov","311"),("data.baltimorecity.gov","311"),("data.austintexas.gov","311")]:
    d=get(f"https://{host}/api/catalog/v1?"+urllib.parse.urlencode({"q":q,"limit":8}))
    print("==",host)
    if isinstance(d,dict) and "__err" in d: print("  ",d); continue
    for r in d.get("results",[])[:8]:
        print("  ",r["resource"]["id"],"|",r["resource"]["name"])
