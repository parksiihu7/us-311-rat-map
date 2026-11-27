import json, urllib.parse, urllib.request, sys
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
def vocab(base,col,tag):
    d=get(base+"?"+urllib.parse.urlencode({"$select":f"{col}, count(*) as n","$group":col,"$order":"n DESC","$limit":1000,"$offset":0}))
    if isinstance(d,dict): print(tag,"ERR",d); return []
    rows=[(r[col],int(r["n"])) for r in d]
    print(tag,"n_types",len(rows))
    for k,n in rows:
        print(f"  {tag}\t{n}\t{k}")
    return rows
vocab("https://data.seattle.gov/resource/5ngg-rpne.json","webintakeservicerequests","SEA")
vocab("https://data.lacity.org/resource/rq3b-xjk8.json","requesttype","LA2020")
