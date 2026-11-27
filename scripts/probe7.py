import json, urllib.parse, urllib.request
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}

print("== BOSTON CKAN")
d=get("https://data.boston.gov/api/3/action/package_show?id=311-service-requests")
if isinstance(d,dict) and "__err" in d: print(d)
else:
    r=d["result"]; print(r.get("title"), len(r.get("resources",[])))
    for res in r.get("resources",[])[:20]: print("  ",res.get("id"),"|",res.get("name"),"|",res.get("format"))
print("== DC layers")
d=get("https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/MapServer?f=json")
if isinstance(d,dict) and "__err" in d: print(d)
else:
    for l in d.get("layers",[]): print("  ",l["id"],"|",l["name"])
