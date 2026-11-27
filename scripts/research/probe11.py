import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def ags(base, params):
    return get(base+"/query?"+urllib.parse.urlencode(params))

svc = {
 "BALT_YEARLY":"https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer",
 "DETROIT":"https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/improve_detroit/FeatureServer/0",
 "PHILLY":"https://services3.arcgis.com/dty2kHktVXHrqO8i/ArcGIS/rest/services/Data_311/FeatureServer/0",
 "DC2025":"https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/18",
}
d=get(svc["BALT_YEARLY"]+"?f=json")
print("BALT layers:", [(l["id"],l["name"]) for l in d.get("layers",[])] if "layers" in d else d)
for k in ["DETROIT","PHILLY","DC2025"]:
    d=get(svc[k]+"?f=json")
    if "__err" in d: print(k,d); continue
    flds=[(f["name"],f["type"]) for f in d.get("fields",[])]
    print(k,"maxRecordCount",d.get("maxRecordCount"))
    print("  fields:",[n for n,_ in flds][:45])
