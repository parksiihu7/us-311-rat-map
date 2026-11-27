import json, urllib.parse, urllib.request
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
print("== BOSTON datastore 2026")
d=get("https://data.boston.gov/api/3/action/datastore_search?resource_id=1a0b420d-99f1-4887-9851-990b2a5a6e17&limit=2")
print(json.dumps(d,ensure_ascii=False)[:1200])
print("== hub search baltimore")
for q in ["311 Customer Service Requests Baltimore","Improve Detroit Issues","311 Service Requests Philadelphia"]:
    d=get("https://hub.arcgis.com/api/v3/datasets?"+urllib.parse.urlencode({"q":q,"page[size]":5}))
    print("--",q)
    for r in (d.get("data") or [])[:5]:
        a=r.get("attributes",{})
        print("   ",a.get("name"),"|",a.get("url"),"|",a.get("recordCount"))
