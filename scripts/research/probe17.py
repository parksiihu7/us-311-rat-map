import json, urllib.parse, urllib.request
def get(url, timeout=90):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except Exception as e: return {"__err":str(e)}
cands={
 "cambridge":"https://data.cambridgema.gov/resource/2z9k-mv9g.json",
 "somerville":"https://data.somervillema.gov/resource/4pyi-uqq6.json",
 "berkeley":"https://data.cityofberkeley.info/resource/p88g-6gs2.json",
 "gainesville":"https://data.cityofgainesville.org/resource/78uv-94ar.json",
 "honolulu":"https://data.honolulu.gov/resource/jdy7-ftwe.json",
 "batonrouge":"https://data.brla.gov/resource/7ixm-mnvx.json",
 "brla_mosq":"https://data.brla.gov/resource/bktv-u9ua.json",
 "norfolk":"https://data.norfolk.gov/resource/nbyu-xjez.json",
 "oakland":"https://data.oaklandca.gov/resource/quth-gb8e.json",
 "kc_new":"https://data.kcmo.org/resource/d4px-6rwg.json",
 "dallas_new":"https://www.dallasopendata.com/resource/d7e7-envw.json",
 "smc":"https://datahub.smcgov.org/resource/4u6x-x6rk.json",
 "bloomington":"https://data.bloomington.in.gov/resource/aw6y-t4ix.json",
}
for n,u in cands.items():
    d=get(u+"?"+urllib.parse.urlencode({"$limit":1}))
    if isinstance(d,dict) and "__err" in d: print(n,"ERR",d["__err"]); continue
    if not d: print(n,"EMPTY"); continue
    print(n, list(d[0].keys()))
