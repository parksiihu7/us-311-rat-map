import json, urllib.parse, urllib.request
def get(url, timeout=45):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
hosts=["data.cincinnati-oh.gov","data.kcmo.org","data.nola.gov","data.nashville.gov","www.dallasopendata.com","data.sanjoseca.gov","data.norfolk.gov","data.baltimorecity.gov","data.hartford.gov","data.cityofnewyork.us"]
for h in hosts:
    d=get(f"https://{h}/api/views.json?"+urllib.parse.urlencode({"limit":100,"q":"311"}))
    print("==",h)
    if isinstance(d,dict) and "__err" in d: print("  ",d["__err"]); continue
    for v in d[:20]:
        n=v.get("name","")
        if "311" in n or "service request" in n.lower() or "service call" in n.lower():
            print("  ",v.get("id")[:9],"|",n[:80],"|",v.get("viewType"))
