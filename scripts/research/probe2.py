import json, urllib.parse, urllib.request, time
def get(base, params, timeout=45):
    url = base + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return None, str(e)

def count(base, where):
    s,d = get(base, {"$select":"count(*)","$where":where})
    return s, (d[0]["count"] if isinstance(d,list) and d else d)

tests = [
 ("chi", "https://data.cityofchicago.org/resource/v6vf-nfxy.json", "upper(sr_type) like '%RODENT%'"),
 ("sf", "https://data.sfgov.org/resource/vw6y-z8j6.json", "upper(service_name) like '%RODENT%'"),
 ("sf2", "https://data.sfgov.org/resource/vw6y-z8j6.json", "upper(service_subtype) like '%RAT%' OR upper(service_name) like '%RAT%'"),
 ("la", "https://data.lacity.org/resource/pvft-t768.json", "upper(requesttype) like '%RAT%'"),
 ("austin", "https://data.austintexas.gov/resource/xwdj-i9he.json", "upper(sr_type_desc) like '%RODENT%'"),
]
for n,b,w in tests:
    print(n, count(b,w))
# sample rows to learn column names
for n,b in [("sea","https://data.seattle.gov/resource/33kz-ixgy.json"),
            ("sf","https://data.sfgov.org/resource/vw6y-z8j6.json"),
            ("chi","https://data.cityofchicago.org/resource/v6vf-nfxy.json"),
            ("la","https://data.lacity.org/resource/pvft-t768.json"),
            ("austin","https://data.austintexas.gov/resource/xwdj-i9he.json")]:
    s,d = get(b, {"$limit":1})
    print(n, s, json.dumps(d, ensure_ascii=False)[:800] if s else d)
