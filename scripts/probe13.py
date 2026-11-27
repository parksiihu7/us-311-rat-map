import json, urllib.parse, urllib.request
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}

# SF vocab
d=get("https://data.sfgov.org/resource/vw6y-z8j6.json?"+urllib.parse.urlencode({"$select":"service_name, count(*) as n","$group":"service_name","$order":"n DESC","$limit":120}))
print("SF names:", [(r["service_name"],r["n"]) for r in d][:60] if isinstance(d,list) else d)
for kw in ["rodent","rat"]:
    d=get("https://data.sfgov.org/resource/vw6y-z8j6.json?"+urllib.parse.urlencode({"$q":kw,"$limit":2}))
    print("SF $q",kw,"->", json.dumps(d,ensure_ascii=False)[:400] if isinstance(d,list) else d)
# Philly carto
for tbl in ["public_cases_fc","requests"]:
    d=get(f"https://phl.carto.com/api/v2/sql?q="+urllib.parse.quote(f"select count(*) from {tbl} where service_name ilike '%rodent%'"))
    print("PHL carto",tbl,d if not isinstance(d,list) else d)
# WPRDC
d=get("https://data.wprdc.org/api/3/action/package_search?q=311&rows=10")
print("WPRDC:", [(p["name"],p["title"]) for p in d.get("result",{}).get("results",[])] if "result" in d else d)
