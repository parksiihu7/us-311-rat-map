import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def socrata(base, params):
    return get(base+"?"+urllib.parse.urlencode(params, quote_via=urllib.parse.quote))
# NYC old
for ds in ["76ig-c548","erm2-nwe9"]:
    b=f"https://data.cityofnewyork.us/resource/{ds}.json"
    print("NYC",ds, socrata(b,{"$select":"count(*)","$where":"complaint_type='Rodent'"}),
          socrata(b,{"$select":"min(created_date), max(created_date)","$where":"complaint_type='Rodent'"}))
# Chicago historical
b="https://data.cityofchicago.org/resource/97t6-zrhs.json"
print("CHI HIST sample:", json.dumps(get(b+"?$limit=1"),ensure_ascii=False)[:600])
print("CHI HIST dates:", socrata(b,{"$select":"min(creation_date), max(creation_date), count(*)"}) if True else None)
# Chicago main types
b2="https://data.cityofchicago.org/resource/v6vf-nfxy.json"
print("CHI main:", socrata(b2,{"$select":"sr_type, count(*) as n","$where":"upper(sr_type) like '%RODENT%'","$group":"sr_type","$order":"n DESC"}))
print("CHI dup:", socrata(b2,{"$select":"count(*)","$where":"upper(sr_type) like '%RODENT%' and duplicate=false"}))
print("CHI dates:", socrata(b2,{"$select":"min(created_date), max(created_date)","$where":"upper(sr_type) like '%RODENT%'"}))
# Baltimore 2025 service fields
d=get("https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_2025/FeatureServer/0?f=json")
print("BALT fields:", [f["name"] for f in d.get("fields",[])][:40] if isinstance(d,dict) and "fields" in d else d)
