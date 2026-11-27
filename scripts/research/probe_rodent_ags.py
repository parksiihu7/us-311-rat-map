import json, urllib.parse, urllib.request
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
for q in ['title:"rodent" AND type:"Feature Service"',
          'title:"rat complaint" AND type:"Feature Service"',
          'title:"rodent complaints"']:
    d=get("https://www.arcgis.com/sharing/rest/search?"+urllib.parse.urlencode({"q":q,"num":40,"f":"json","sortField":"numviews","sortOrder":"desc"}))
    print("==",q,"total",d.get("total"))
    for r in (d.get("results") or [])[:25]:
        print(f"  {r.get('owner'):22s} | {r.get('title')[:55]:55s} | {r.get('url','')[:95]}")
