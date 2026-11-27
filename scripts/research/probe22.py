import json, urllib.parse, urllib.request, re
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
print("BR types:", get("https://data.brla.gov/resource/bktv-u9ua.json?"+urllib.parse.urlencode({"$select":"type, count(*) as n","$group":"type","$order":"n DESC","$limit":20})))
print("BR sample:", json.dumps(get("https://data.brla.gov/resource/bktv-u9ua.json?$limit=2"),ensure_ascii=False)[:900])
d=get("https://data.montgomerycountymd.gov/api/views.json?limit=400")
if isinstance(d,list):
    print("MC views:", [(v.get("id"),v.get("name")) for v in d if re.search(r"311|service request",(v.get("name") or ""),re.I)][:10])
else: print("MC", d)
