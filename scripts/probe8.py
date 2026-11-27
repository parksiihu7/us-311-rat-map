import json, urllib.parse, urllib.request
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}

def top(base, col, kw=("RAT","RODENT"), limit=300):
    d=get(base+"?"+urllib.parse.urlencode({"$select":f"{col}, count(*) as n","$group":col,"$order":"n DESC","$limit":limit}))
    if isinstance(d,dict) and "__err" in d: return d
    return [(r[col], int(r["n"])) for r in d if any(k in (r[col] or "").upper() for k in kw)]

print("SEA:", top("https://data.seattle.gov/resource/5ngg-rpne.json","webintakeservicerequests"))
print("LA2020:", top("https://data.lacity.org/resource/rq3b-xjk8.json","requesttype"))
print("LA2022:", top("https://data.lacity.org/resource/i5ke-k6by.json","requesttype"))
print("AUS:", top("https://data.austintexas.gov/resource/xwdj-i9he.json","sr_type_desc"))
print("SF:", top("https://data.sfgov.org/resource/vw6y-z8j6.json","service_name"), top("https://data.sfgov.org/resource/vw6y-z8j6.json","service_subtype"))
print("NYC:", top("https://data.cityofnewyork.us/resource/erm2-nwe9.json","complaint_type", ("RODENT",)), top("https://data.cityofnewyork.us/resource/erm2-nwe9.json","descriptor",("RAT",)))
print("CHI:", top("https://data.cityofchicago.org/resource/v6vf-nfxy.json","sr_type",("RODENT","RAT")))
print("BOSTON datastore:", get("https://data.boston.gov/api/3/action/datastore_search?resource_id=1a0b420d-99f1-4887-9851-990b2a5a6e17&limit=1"))
