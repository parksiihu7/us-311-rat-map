import json, urllib.parse, urllib.request, re
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def ags(base, params):
    p=dict(params); p["f"]="json"
    return get(base.rstrip('/')+"/query?"+urllib.parse.urlencode(p))
def probe(name, svc):
    meta=get(svc+"?f=json")
    if "__err" in meta: print(name,"ERR",meta["__err"]); return
    # if service (has layers) take layer 0
    if "layers" in meta and meta["layers"]:
        lid=meta["layers"][0]["id"]; base=svc+"/"+str(lid)
        meta=get(base+"?f=json")
    else: base=svc
    if "__err" in meta: print(name,"ERR2",meta["__err"]); return
    flds=[f for f in meta.get("fields",[])]
    strf=[f["name"] for f in flds if f["type"]=="esriFieldTypeString"]
    print(f"{name} maxRec {meta.get('maxRecordCount')} strfields {strf[:25]}")
    # try each candidate type field
    for cand in [f for f in strf if re.search(r"type|name|category|subject|service|issue|problem", f, re.I)][:6]:
        r=ags(base,{"where":f"upper({cand}) like '%RODENT%' OR upper({cand}) like '%RAT%'","outFields":cand,"returnDistinctValues":"true","returnGeometry":"false"})
        vals=[f["attributes"][cand] for f in r.get("features",[])] if "features" in r else r
        if isinstance(vals,list) and any(("rat" in (v or "").lower() or "rodent" in (v or "").lower()) for v in vals):
            vals=[v for v in vals if ("rat" in (v or "").lower() or "rodent" in (v or "").lower())]
            c=ags(base,{"where":f"upper({cand}) like '%RODENT%' OR upper({cand}) like '%RAT%'","returnCountOnly":"true"})
            print(f"   -> {cand}: {c}  sample={vals[:6]}")
            break
probe("DENVER","https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_service_requests_311/FeatureServer")
probe("NASHVILLE","https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/hubNashville_(311)_Service_Requests_1/FeatureServer")
probe("LOUISVILLE2025","https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/metro_311_2025/FeatureServer")
probe("MIAMIDADE2023","https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/data_311_2023/FeatureServer")
probe("HOUSTON","https://mycity2.houstontx.gov/gisweb01/rest/services/311/HOUSTON311_RECENT_SR_SNOW/FeatureServer")
probe("LEXINGTON","https://services1.arcgis.com/Mg7DLdfYcSWIaDnu/arcgis/rest/services/CitizenRequests_public/FeatureServer")
