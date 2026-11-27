import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}

cities=["Minneapolis","Denver","Houston","Pittsburgh","New Orleans","Milwaukee","Columbus","Cleveland","San Diego","Nashville","Cincinnati","Dallas","Kansas City","St. Louis","Buffalo","Rochester","Hartford","Sacramento","Oakland","Long Beach"]
for c in cities:
    d=get("https://hub.arcgis.com/api/v3/datasets?"+urllib.parse.urlencode({"q":f"{c} 311 service requests","page[size]":8}))
    print("==",c)
    if "__err" in d: print("  ",d); continue
    shown=0
    for r in d.get("data") or []:
        a=r.get("attributes",{})
        u=a.get("url") or ""
        rc=a.get("recordCount") or 0
        if "/FeatureServer" in u and rc>3000:
            print(f"   {a.get('name')[:60]} | {u} | {rc}")
            shown+=1
        if shown>=3: break
