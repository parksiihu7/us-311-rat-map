import json, urllib.parse, urllib.request, re
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def ags(base, params):
    p=dict(params); p["f"]="json"
    return get(base.rstrip('/')+"/query?"+urllib.parse.urlencode(p))
RAT=re.compile(r"\b(rats?|rodents?|rodent control|rat control)\b", re.I)
def listing(name,svc,fld):
    r=ags(svc,{"where":"1=1","outFields":fld,"returnDistinctValues":"true","returnGeometry":"false","returnExceededLimitFeatures":"true"})
    if "features" not in r: print(name,fld,"ERR",str(r)[:200]); return
    vals=[f["attributes"][fld] for f in r["features"]]
    hits=[v for v in vals if v and RAT.search(v)]
    print(f"{name}: {len(vals)} distinct, rat-ish={hits[:12]}")
    if hits:
        for v in hits:
            c=ags(svc,{"where":f"{fld}='{v.replace(chr(39),chr(39)*2)}'","returnCountOnly":"true"})
            print("     ",v,c)
DEN="https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_service_requests_311/FeatureServer/0"
listing("DENVER",DEN,"CASE_TYPE") if False else None
d=get("https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_service_requests_311/FeatureServer?f=json")
print("DEN layers", d.get("layers"))
for lid in [l["id"] for l in d.get("layers",[])][:3]:
    m=get(f"https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_service_requests_311/FeatureServer/{lid}?f=json")
    print("  layer",lid,m.get("name"),[f["name"] for f in m.get("fields",[])][:30])
