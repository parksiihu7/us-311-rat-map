import json, urllib.parse, urllib.request, re
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def ags(base, params):
    p=dict(params); p["f"]="json"
    return get(base.rstrip('/')+"/query?"+urllib.parse.urlencode(p))
RAT=re.compile(r"(rats?|rodents?)\b", re.I)
def listing(name,svc,fld):
    r=ags(svc,{"where":"1=1","outFields":fld,"returnDistinctValues":"true","returnGeometry":"false"})
    if "features" not in r: print(name,fld,"ERR",str(r)[:160]); return
    vals=[f["attributes"][fld] for f in r["features"]]
    hits=sorted({v for v in vals if v and RAT.search(v)})
    print(f"{name}: {len(vals)} distinct, hits={hits[:10]}")
    for v in hits[:6]:
        c=ags(svc,{"where":f"{fld}='{v.replace(chr(39),chr(39)*2)}'","returnCountOnly":"true"})
        print("    ",v, c.get("count") if isinstance(c,dict) else c)
listing("LOUISVILLE2025","https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/metro_311_2025/FeatureServer/0","service_name")
listing("NASHVILLE","https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/hubNashville_(311)_Service_Requests_1/FeatureServer/0","Request_Type")
listing("HOUSTON","https://mycity2.houstontx.gov/gisweb01/rest/services/311/HOUSTON311_RECENT_SR_SNOW/FeatureServer/0","CASE_TYPE")
d=get("https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/data_311_2023/FeatureServer?f=json")
print("MIA layers",[l["name"] for l in d.get("layers",[])][:5] if isinstance(d,dict) else d)
