import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def types(base,col,kws=("RAT","RODENT")):
    cond=" OR ".join(f"upper({col}) like '%{k}%'" for k in kws)
    d=get(base+"?"+urllib.parse.urlencode({"$select":f"{col}, count(*) as n","$where":cond,"$group":col,"$order":"n DESC","$limit":30}))
    if isinstance(d,dict): return d
    return [(r[col],int(r["n"])) for r in d]
tests={
 "CAMBRIDGE":("https://data.cambridgema.gov/resource/2z9k-mv9g.json","issue_type"),
 "SOMERVILLE":("https://data.somervillema.gov/resource/4pyi-uqq6.json","type"),
 "SOMERVILLE_CL":("https://data.somervillema.gov/resource/4pyi-uqq6.json","classification"),
 "BERKELEY":("https://data.cityofberkeley.info/resource/p88g-6gs2.json","case_request"),
 "GAINESVILLE":("https://data.cityofgainesville.org/resource/78uv-94ar.json","request_type"),
 "BATONROUGE":("https://data.brla.gov/resource/7ixm-mnvx.json","typename"),
 "DALLAS_NEW":("https://www.dallasopendata.com/resource/d7e7-envw.json","service_request_type"),
 "SMC":("https://datahub.smcgov.org/resource/4u6x-x6rk.json","request_type"),
 "BLOOMINGTON":("https://data.bloomington.in.gov/resource/aw6y-t4ix.json","service_name"),
 "NORFOLK":("https://data.norfolk.gov/resource/nbyu-xjez.json","service_request_type"),
 "OAKLAND":("https://data.oaklandca.gov/resource/quth-gb8e.json","reqcategory"),
}
for n,(b,c) in tests.items():
    print(n, types(b,c))
