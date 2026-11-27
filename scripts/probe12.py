import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def ags(base, params):
    p=dict(params); p["f"]="json"
    return get(base+"/query?"+urllib.parse.urlencode(p))

DET="https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/improve_detroit/FeatureServer/0"
PHL="https://services3.arcgis.com/dty2kHktVXHrqO8i/ArcGIS/rest/services/Data_311/FeatureServer/0"
BALT="https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/0"

print("DET count rodent:", ags(DET,{"where":"request_type like '%Rodent%'","returnCountOnly":"true"}))
print("DET types:", json.dumps(ags(DET,{"where":"request_type like '%Rodent%'","outFields":"request_type","returnDistinctValues":"true","returnGeometry":"false"}),ensure_ascii=False)[:400])
print("PHL rat count:", ags(PHL,{"where":"upper(service_name) like '%RODENT%' OR upper(service_name) like '%RAT%'","returnCountOnly":"true"}))
print("PHL svcnames:", json.dumps(ags(PHL,{"where":"upper(service_name) like '%RODENT%' OR upper(service_name) like '%RAT%'","outFields":"service_name","returnDistinctValues":"true","returnGeometry":"false"}),ensure_ascii=False)[:600])
print("PHL dates:", ags(PHL,{"where":"1=1","outStatistics":json.dumps([{"statisticType":"min","onStatisticField":"requested_datetime","outStatisticFieldName":"mn"},{"statisticType":"max","onStatisticField":"requested_datetime","outStatisticFieldName":"mx"},{"statisticType":"count","onStatisticField":"service_request_id","outStatisticFieldName":"c"}]),"returnGeometry":"false"}))
print("BALT2022 srtypes:", json.dumps(ags(BALT,{"where":"upper(SRType) like '%RAT%' OR upper(SRType) like '%RODENT%'","outFields":"SRType","returnDistinctValues":"true","returnGeometry":"false"}),ensure_ascii=False)[:800])
for yr,lid in [("2020",11),("2021",12),("2022",14),("2023",15),("2024",16),("2025",18),("2026",21)]:
    u=f"https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/{lid}"
    r=ags(u,{"where":"SERVICECODEDESCRIPTION IN ('Rodent Inspection and Treatment','DC Health Rodent & Vector Control')","returnCountOnly":"true"})
    print("DC",yr,r)
