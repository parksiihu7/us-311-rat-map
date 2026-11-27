import json, urllib.parse, urllib.request, re
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
# PHL distinct pest names
d=get("https://phl.carto.com/api/v2/sql?q="+urllib.parse.quote("select service_name, count(*) c from public_cases_fc where service_name ilike '%pest%' or service_name ilike '%rat%' or service_name ilike '%rodent%' or service_name ilike '%vector%' group by service_name order by c desc limit 20"))
print("PHL:", d if not isinstance(d,list) else d)
# WPRDC resources
d=get("https://data.wprdc.org/api/3/action/package_show?id=pittsburgh-311-data")
if "result" in d:
    for r in d["result"]["resources"][:10]: print("WPRDC res:", r.get("name"), r.get("id"), r.get("datastore_active"))
else: print(d)
# Socrata portal views list, all
hosts=["data.cincinnati-oh.gov","data.kcmo.org","data.nola.gov","data.nashville.gov","www.dallasopendata.com","data.sanjoseca.gov","data.detroitmi.gov","data.milwaukee.gov","data.cityofchicago.org"]
for h in hosts:
    d=get(f"https://{h}/api/views.json?limit=500&offset=0")
    print("==",h, "type", type(d).__name__)
    if isinstance(d,dict) and "__err" in d: print("   ",d["__err"]); continue
    hits=[(v.get("id"),v.get("name")) for v in d if re.search(r"311|service request|service call", (v.get("name") or ""), re.I)]
    for x in hits[:12]: print("   ",x)
