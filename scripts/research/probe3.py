import json, urllib.parse, urllib.request, time
def get(url, timeout=50):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}

# Socrata catalog search for 311 service request datasets
for dom, q in [("data.seattle.gov","311 customer service requests"),
               ("data.baltimorecity.gov","311"),
               ("data.lacity.org","311"),
               ("data.austintexas.gov","rat rodent"),
               ("data.cityofchicago.org","311")]:
    d = get("https://api.us.socrata.com/api/catalog/v1?"+urllib.parse.urlencode({"domains":dom,"q":q,"limit":6}))
    print("==",dom,q)
    for r in d.get("results",[])[:6]:
        res=r["resource"]
        print("  ",res["id"],"|",res["name"],"|",res.get("updatedAt"),"| rows:",(r.get("metadata") or {}).get("rowsUpdatedAt"))
