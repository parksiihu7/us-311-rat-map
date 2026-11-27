import json, urllib.parse, urllib.request, re, sys
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def ags(base, params):
    p=dict(params); p["f"]="json"
    return get(base.rstrip('/')+"/query?"+urllib.parse.urlencode(p))
RAT=re.compile(r"(rats?|rodents?)\b", re.I)
def check(name, svc):
    meta=get(svc.rstrip('/')+"?f=json")
    if "__err" in meta: return print(f"{name}: ERR {meta['__err']}")
    base=svc
    if meta.get("layers"):
        base=svc.rstrip('/')+"/"+str(meta["layers"][0]["id"]); meta=get(base+"?f=json")
    flds=[f["name"] for f in meta.get("fields",[]) if f["type"]=="esriFieldTypeString"]
    if not flds: return print(f"{name}: no str fields")
    cand=[f for f in flds if re.search(r"(type|category|name|subject|service|issue|problem|request)",f,re.I)][:5]
    found=[]
    for f in cand:
        r=ags(base,{"where":"1=1","outFields":f,"returnDistinctValues":"true","returnGeometry":"false"})
        if "features" not in r: continue
        vals=[x["attributes"][f] for x in r["features"]]
        hits=[v for v in vals if v and RAT.search(v)]
        if hits:
            for v in hits[:4]:
                c=ags(base,{"where":f"{f}='{v.replace(chr(39),chr(39)*2)}'","returnCountOnly":"true"})
                found.append((f,v,c.get("count") if isinstance(c,dict) else None))
    print(f"{name}: base={base} maxRec={meta.get('maxRecordCount')} -> {found}")
    return found
city_queries={
 "Phoenix":'title:"311" AND owner:CityofPhoenixAZ',
 "Minneapolis":'title:"311" AND (title:"request" OR title:"Request")=' ,
}
# direct searches
searches={
 "PHOENIX":'title:"311" AND title:"Request" AND (owner:CityofPhoenixAZ OR owner:CITYOFPHOENIX)',
 "MINNEAPOLIS":'title:"311" AND owner:*minneap*',
 "MILWAUKEE":'title:"311" AND owner:*milwaukee*',
 "CLEVELAND":'title:"311" AND owner:*cleveland*',
 "COLUMBUS":'title:"311" AND owner:*columbus*',
 "SANANTONIO":'title:"311" AND owner:*sanantonio*',
 "SANDIEGO":'title:"311" AND owner:*sandiego*',
 "SACRAMENTO":'title:"311" AND owner:*sacramento*',
 "KANSASCITY":'title:"311" AND owner:*kcmo*',
 "ALBUQUERQUE":'title:"311" AND owner:*cabq*',
 "TUCSON":'title:"311" AND owner:*tucson*',
}
for n,q in searches.items():
    d=get("https://www.arcgis.com/sharing/rest/search?"+urllib.parse.urlencode({"q":q,"num":5,"f":"json"}))
    print("==",n, d.get("total") if isinstance(d,dict) else d)
    for r in (d.get("results") or [])[:3]:
        print("   ",r.get("title"),"|",r.get("url"))
