import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def sample(base, n=1):
    d=get(base+"?"+urllib.parse.urlencode({"$limit":n}))
    return list(d[0].keys()) if isinstance(d,list) and d else d
for name,u in [("CINCI","https://data.cincinnati-oh.gov/resource/gcej-gmiw.json"),
               ("KC","https://data.kcmo.org/resource/r88q-eyb8.json"),
               ("NOLA","https://data.nola.gov/resource/2jgv-pqrq.json"),
               ("DALLAS","https://www.dallasopendata.com/resource/4n3h-rfqm.json"),
               ("DALLAS2","https://www.dallasopendata.com/resource/i2q3-6wr4.json")]:
    print(name, sample(u))
d=get("https://data.wprdc.org/api/3/action/datastore_search?resource_id=5202679a-d243-402e-b82a-63189995a942&limit=1")
print("WPRDC fields:", [f["id"] for f in d["result"]["fields"]] if "result" in d else d)
d=get("https://phl.carto.com/api/v2/sql?q="+urllib.parse.quote("select service_name, count(*) c from public_cases_fc group by service_name order by c desc limit 40"))
print("PHL top:", d.get("rows") if isinstance(d,dict) else d)
