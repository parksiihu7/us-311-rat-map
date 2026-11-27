import json, urllib.parse, urllib.request
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def q(base, params):
    return get(base+"?"+urllib.parse.urlencode(params, quote_via=urllib.parse.quote))
def types(base, col, kw):
    d=q(base, {"$select":f"{col}, count(*) as n","$where":f"upper({col}) like '%{kw}%'","$group":col,"$order":"n DESC","$limit":50})
    if isinstance(d,dict): return d
    return [(r[col],int(r["n"])) for r in d]
print("SEA rat:", types("https://data.seattle.gov/resource/5ngg-rpne.json","webintakeservicerequests","RAT"))
print("LA2020 rat:", types("https://data.lacity.org/resource/rq3b-xjk8.json","requesttype","RAT"))
print("LA2022 rat:", types("https://data.lacity.org/resource/i5ke-k6by.json","requesttype","RAT"))
print("AUS rat:", types("https://data.austintexas.gov/resource/xwdj-i9he.json","sr_type_desc","RAT"))
print("SF subtype rat:", types("https://data.sfgov.org/resource/vw6y-z8j6.json","service_subtype","RAT"))
print("SF name rat:", types("https://data.sfgov.org/resource/vw6y-z8j6.json","service_name","RAT"))
print("CHI rat:", types("https://data.cityofchicago.org/resource/v6vf-nfxy.json","sr_type","RAT"))
