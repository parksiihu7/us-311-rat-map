import json, urllib.parse, urllib.request, sys, time
def get(url, timeout=40):
    req=urllib.request.Request(url, headers={"User-Agent":"rat-map-research/1.0","Accept":"application/json"})
    t=time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b=r.read()
            return r.status, json.loads(b), time.time()-t
    except Exception as e:
        return None, str(e), time.time()-t

probes = {
 "nyc_2020": "https://data.cityofnewyork.us/resource/erm2-nwe9.json?$select=count(*)&$where=complaint_type='Rodent'",
 "nyc_2010": "https://data.cityofnewyork.us/resource/fhrw-4uyv.json?$select=count(*)&$where=complaint_type='Rodent'",
 "chi": "https://data.cityofchicago.org/resource/v6vf-nfxy.json?$select=count(*)&$where=upper(sr_type) like '%25RODENT%25'",
 "sf": "https://data.sfgov.org/resource/vw6y-z8j6.json?$select=count(*)",
 "sf_rodent": "https://data.sfgov.org/resource/vw6y-z8j6.json?$select=count(*)&$where=upper(service_name) like '%25RODENT%25'",
 "sea": "https://data.seattle.gov/resource/33kz-ixgy.json?$select=count(*)",
 "la": "https://data.lacity.org/resource/pvft-t768.json?$select=count(*)",
 "austin": "https://data.austintexas.gov/resource/xwdj-i9he.json?$select=count(*)",
 "balt": "https://data.baltimorecity.gov/resource/9agw-sxsr.json?$select=count(*)",
}
for k,u in probes.items():
    s,d,el=get(u)
    print(k, s, str(d)[:300], f"{el:.1f}s")
