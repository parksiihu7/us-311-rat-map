import json, urllib.parse, urllib.request
def get(url, timeout=120):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def soc(base, where):
    return get(base+"?"+urllib.parse.urlencode({"$select":"date_trunc_ym(created_date) as m, count(*) as n","$where":where,"$group":"m","$order":"m","$limit":300}, quote_via=urllib.parse.quote))
print("NYC_old:", soc("https://data.cityofnewyork.us/resource/76ig-c548.json","complaint_type='Rodent'"))
print("CHI_HIST:", get("https://data.cityofchicago.org/resource/97t6-zrhs.json?"+urllib.parse.urlencode({"$select":"date_trunc_y(creation_date) as y, count(*) as n","$group":"y","$order":"y","$limit":100},quote_via=urllib.parse.quote)))
print("CINCI range:", soc("https://data.cincinnati-oh.gov/resource/gcej-gmiw.json","sr_type_desc like '%RATS%'"))
print("CAMBRIDGE:", get("https://data.cambridgema.gov/resource/2z9k-mv9g.json?"+urllib.parse.urlencode({"$select":"date_trunc_y(ticket_created_date_time) as y, count(*) as n","$where":"upper(issue_type) like '%RODENT%'","$group":"y","$order":"y","$limit":100},quote_via=urllib.parse.quote)))
print("BRLA:", get("https://data.brla.gov/resource/bktv-u9ua.json?"+urllib.parse.urlencode({"$select":"date_trunc_y(call_in_date) as y, count(*) as n","$where":"type in ('RODENT','BOTH')","$group":"y","$order":"y","$limit":100},quote_via=urllib.parse.quote)))
