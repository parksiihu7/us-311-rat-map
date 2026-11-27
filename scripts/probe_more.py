import json, urllib.parse, urllib.request
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def q(base, params):
    return get(base+"?"+urllib.parse.urlencode(params, quote_via=urllib.parse.quote))
# NOLA request types containing rodent
print("NOLA:", q("https://data.nola.gov/resource/2jgv-pqrq.json", {"$select":"request_type, count(*) as n","$where":"upper(request_type) like '%RODENT%' OR upper(request_type) like '%RAT%'","$group":"request_type","$limit":20}))
print("NOLA reasons:", q("https://data.nola.gov/resource/2jgv-pqrq.json", {"$select":"request_reason, count(*) as n","$where":"upper(request_reason) like '%RODENT%' OR upper(request_reason) like '%RAT%'","$group":"request_reason","$limit":20}))
# KC public works 311 issues
print("KC sample:", list(get("https://data.kcmo.org/resource/pupn-3wnn.json?$limit=1")[0].keys()) if isinstance(get("https://data.kcmo.org/resource/pupn-3wnn.json?$limit=1"), list) else get("https://data.kcmo.org/resource/pupn-3wnn.json?$limit=1"))
# SF details
print("SF details:", q("https://data.sfgov.org/resource/vw6y-z8j6.json", {"$select":"service_details, count(*) as n","$where":"upper(service_details) like '%RODENT%' OR upper(service_details) like '%RAT%'","$group":"service_details","$order":"n DESC","$limit":10}))
# Buffalo portal views
d=get("https://data.buffalony.gov/api/views.json?limit=400")
print("BUFFALO views:", [(v.get("id"),v.get("name")) for v in d if v and ("311" in (v.get("name") or "") or "service" in (v.get("name") or "").lower())][:10] if isinstance(d,list) else d)
