import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def socrata_types(base, col, kw="RAT"):
    d=get(base+"?"+urllib.parse.urlencode({"$select":f"{col}, count(*) as n","$where":f"upper({col}) like '%{kw}%'","$group":col,"$order":"n DESC","$limit":40}))
    if isinstance(d,dict): return d
    return [(r[col],int(r["n"])) for r in d]
print("CINCI rat:", socrata_types("https://data.cincinnati-oh.gov/resource/gcej-gmiw.json","sr_type_desc"))
print("NOLA rat:", socrata_types("https://data.nola.gov/resource/2jgv-pqrq.json","request_type"))
print("DALLAS rat:", socrata_types("https://www.dallasopendata.com/resource/4n3h-rfqm.json","service_request_type"))
q=urllib.parse.quote('SELECT subject, count(*) as n FROM "5202679a-d243-402e-b82a-63189995a942" WHERE subject ILIKE \'%rodent%\' OR subject ILIKE \'%rat%\' GROUP BY subject ORDER BY n DESC')
d=get("https://data.wprdc.org/api/3/action/datastore_search_sql?sql="+q)
print("PITTS:", [ (r["subject"],r["n"]) for r in d["result"]["records"]] if "result" in d else d)
