import json, urllib.parse, urllib.request
def q(base, params):
    url=base+"?"+urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
SF="https://data.sfgov.org/resource/vw6y-z8j6.json"
print("SF details rodent:", q(SF, {"$select":"service_details, count(*) as n","$where":"upper(service_details) like '%RODENT%'","$group":"service_details","$order":"n DESC"}))
print("SF count:", q(SF, {"$select":"count(*)","$where":"service_details='Infestation_Rodent_Insect'"}))
print("SF range:", q(SF, {"$select":"min(requested_datetime), max(requested_datetime)","$where":"service_details='Infestation_Rodent_Insect'"}))
print("SF row:", q(SF, {"$where":"service_details='Infestation_Rodent_Insect'","$limit":1}))
NOLA="https://data.nola.gov/resource/2jgv-pqrq.json"
w="request_type='Mosquito, Termite & Rodent Control' AND request_reason IN ('Rodent Complaint (Mice & Rats)','Rodent Complaint (Rats)')"
print("NOLA count:", q(NOLA, {"$select":"count(*)","$where":w}))
print("NOLA range:", q(NOLA, {"$select":"min(date_created), max(date_created)","$where":w}))
print("NOLA row:", q(NOLA, {"$where":w,"$limit":1}))
