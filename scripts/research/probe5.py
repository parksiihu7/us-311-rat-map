import json, urllib.parse, urllib.request, collections
def get(url, timeout=60):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}

socrata = {
 "seattle":"https://data.seattle.gov/resource/5ngg-rpne.json",
 "la2020":"https://data.lacity.org/resource/rq3b-xjk8.json",
 "la2022":"https://data.lacity.org/resource/i5ke-k6by.json",
 "cincy":"https://data.cincinnati-oh.gov/resource/gcej-8x2h.json",
 "kcmo":"https://data.kcmo.org/resource/v6vt-7wdr.json",
 "nola":"https://data.nola.gov/resource/3izj-hm2u.json",
 "nashville":"https://data.nashville.gov/resource/8s5a-gjm9.json",
 "dallas":"https://www.dallasopendata.com/resource/d7e6-hxtb.json",
 "sjc":"https://data.sanjoseca.gov/resource/d4jp-kh7e.json",
 "norfolk":"https://data.norfolk.gov/resource/qn5u-r4dm.json",
}
for name,base in socrata.items():
    d=get(base+"?$limit=1")
    if isinstance(d,dict) and "__err" in d:
        print(name,"ERR",d["__err"]); continue
    if not d: print(name,"EMPTY"); continue
    print(name, list(d[0].keys()))
