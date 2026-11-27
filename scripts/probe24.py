import json, urllib.parse, urllib.request
def get(url, timeout=120):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def ags(base, params):
    p=dict(params); p["f"]="json"
    return get(base.rstrip('/')+"/query?"+urllib.parse.urlencode(p))
BALT_WHERE="SRType IN ('SW-Rat Rubout','SW-Rat Rubout Follow-up','SW-Rat Rubout Alley Concern (SW creation only)','HCD-Rodents','SW-Rat Rubout Proactive')"
balt_yearly="https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer"
for lid,yr in [(2,2020),(1,2021),(0,2022)]:
    print("BALT",yr, ags(f"{balt_yearly}/{lid}",{"where":BALT_WHERE,"returnCountOnly":"true"}))
for name,url in [("2023","https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_2023/FeatureServer/0"),
                 ("2024","https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_2024/FeatureServer/0"),
                 ("2025","https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_2025/FeatureServer/0"),
                 ("2026","https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_current/FeatureServer/0")]:
    print("BALT",name, ags(url,{"where":BALT_WHERE,"returnCountOnly":"true"}))
# Boston per year rodent counts
res={"2026":"1a0b420d-99f1-4887-9851-990b2a5a6e17","2025":"9d7c2214-4709-478a-a2e8-fb2020a5bb94","2024":"dff4d804-5031-443a-8409-8344efd0e5c8","2023":"e6013a93-1321-4f2a-bf91-8d8a02f1e62f","2022":"81a7b022-f8fc-4da5-80e4-b160058ca207","2021":"f53ebccd-bc61-49f9-83db-625f209c95f5","2020":"6ff6a6fd-3141-4440-a880-6f60a37fe789","2019":"ea2e4696-4a2d-429c-9807-d02eb92e0222","2018":"2be28d90-3a90-4af1-a3f6-f28c1e25880a","2017":"30022137-709d-465e-baae-ca155b51927d","2016":"b7ea6b1b-3ca4-4c5b-9713-6dc1db52379a","2015":"c9509ab4-6f6d-4b97-979a-0cf2a10c922b"}
for y,rid in res.items():
    d=get("https://data.boston.gov/api/3/action/datastore_search_sql?sql="+urllib.parse.quote(f'SELECT count(*) as n FROM "{rid}" WHERE lower(case_title) LIKE \'%rodent%\''))
    print("BOS",y, d.get("result",{}).get("records") if isinstance(d,dict) else d)
