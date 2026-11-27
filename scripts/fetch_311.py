#!/usr/bin/env python3
"""
fetch_311.py - fetch real rat/rodent 311 complaint records from US municipal open data
and write them as compact per-city, per-year JSON files for the web app.

Repeatable: run it again at any time. Finished years are skipped unless --force;
the current year is always refetched. State (counts, coordinate coverage) lives in
scripts/state.json so the manifest always reflects what is on disk.

Usage:
  python3 scripts/fetch_311.py                 # all cities, 2012..today
  python3 scripts/fetch_311.py --city nyc chicago --force
  python3 scripts/fetch_311.py --min-year 2020 --only-current-year
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STATE_PATH = os.path.join(ROOT, "scripts", "state.json")
EPOCH = dt.date(2000, 1, 1)
UA = "us-311-rat-map/1.0 (open-source civic research; contact: parksiihu7@users.noreply.github.com)"
MIN_YEAR_DEFAULT = 2012


def log(*a):
    print(*a, flush=True)


def get_json(url, tries=4, timeout=120):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001 - retried network failures
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {url} -> {last}")


def day_index(d: dt.date) -> int:
    return (d - EPOCH).days


def parse_date(s):
    if not s:
        return None
    s = str(s).strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        try:
            return dt.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
        except ValueError:
            return None
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def coords(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(lat) and math.isfinite(lon)):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    if abs(lat) < 1e-6 and abs(lon) < 1e-6:
        return None
    return round(lat, 5), round(lon, 5)


# ---------------------------------------------------------------- adapters
# Each adapter exposes iter_year(year) -> (records, nocoord_count)
# record = (date, lat, lon, original_classification, resident_flag)
# resident_flag: 1 = resident-initiated report/request, 0 = city-initiated work order


def socrata_pages(dataset, select, where, order=":id", page=50000):
    offset = 0
    while True:
        params = {"$select": select, "$where": where, "$order": order, "$limit": page, "$offset": offset}
        url = f"https://{dataset[0]}/resource/{dataset[1]}.json?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        rows = get_json(url)
        if not rows:
            return
        for row in rows:
            yield row
        if len(rows) < page:
            return
        offset += page
        time.sleep(0.15)


def socrata_count(dataset, where):
    url = (f"https://{dataset[0]}/resource/{dataset[1]}.json?"
           + urllib.parse.urlencode({"$select": "count(*)", "$where": where}, quote_via=urllib.parse.quote))
    d = get_json(url)
    return int(d[0]["count"]) if d else 0


def year_where(datefield, year, extra=None):
    w = f"{datefield} >= '{year}-01-01T00:00:00' AND {datefield} < '{year + 1}-01-01T00:00:00'"
    return f"({extra}) AND {w}" if extra else w


def socrata_adapter(dataset, datefield, typefield, type_where, type_map, coord_field=("latitude", "longitude"),
                    idfield=None, resident=1):
    def iter_year(year):
        select = ",".join([datefield, typefield, coord_field[0], coord_field[1]] + ([idfield] if idfield else []))
        out, nocoord, seen = [], 0, set()
        for row in socrata_pages(dataset, select, year_where(datefield, year, type_where)):
            d = parse_date(row.get(datefield))
            if d is None:
                continue
            c = coords(row.get(coord_field[0]), row.get(coord_field[1]))
            orig = row.get(typefield) or ""
            label = type_map(orig) if callable(type_map) else (type_map.get(orig) or orig)
            if c is None:
                nocoord += 1
                continue
            key = row.get(idfield) if idfield else None
            if key:
                if key in seen:
                    continue
                seen.add(key)
            out.append((d, c[0], c[1], label, resident))
        return out, nocoord
    return iter_year


# ---- New York City -------------------------------------------------------
NYC_TYPES = {"Rodent": "Rodent complaint"}


def nyc_descriptor(row_type, row_desc):
    return f"Rodent / {row_desc}" if row_desc else "Rodent"


def make_socrata_rows_adapter(dataset, datefield, typefield, descfield, type_where, coord_field=("latitude", "longitude"),
                              idfield="unique_key", resident=1):
    def iter_year(year):
        cols = [datefield, typefield] + ([descfield] if descfield else []) + [coord_field[0], coord_field[1], idfield]
        select = ",".join(cols)
        out, nocoord, seen = [], 0, set()
        for row in socrata_pages(dataset, select, year_where(datefield, year, type_where)):
            d = parse_date(row.get(datefield))
            if d is None:
                continue
            c = coords(row.get(coord_field[0]), row.get(coord_field[1]))
            orig = row.get(typefield) or ""
            if descfield and row.get(descfield):
                orig = f"{orig} / {row[descfield]}"
            if not orig:
                continue
            if c is None:
                nocoord += 1
                continue
            key = row.get(idfield)
            if key in seen:
                continue
            seen.add(key)
            out.append((d, c[0], c[1], orig, resident))
        return out, nocoord
    return iter_year


# ---- Boston (CKAN) -------------------------------------------------------
BOS_RES = {
    2012: "382e10d9-1864-40ba-bef6-4eea3c75463c",
    2013: "407c5cd0-f764-4a41-adf8-054ff535049e",
    2014: "bdae89c8-d4ce-40e9-a6e1-a5203953a2e0",
    2015: "c9509ab4-6f6d-4b97-979a-0cf2a10c922b",
    2016: "b7ea6b1b-3ca4-4c5b-9713-6dc1db52379a",
    2017: "30022137-709d-465e-baae-ca155b51927d",
    2018: "2be28d90-3a90-4af1-a3f6-f28c1e25880a",
    2019: "ea2e4696-4a2d-429c-9807-d02eb92e0222",
    2020: "6ff6a6fd-3141-4440-a880-6f60a37fe789",
    2021: "f53ebccd-bc61-49f9-83db-625f209c95f5",
    2022: "81a7b022-f8fc-4da5-80e4-b160058ca207",
    2023: "e6013a93-1321-4f2a-bf91-8d8a02f1e62f",
    2024: "dff4d804-5031-443a-8409-8344efd0e5c8",
    2025: "9d7c2214-4709-478a-a2e8-fb2020a5bb94",
    2026: "1a0b420d-99f1-4887-9851-990b2a5a6e17",
}


def ckan_sql(sql):
    url = "https://data.boston.gov/api/3/action/datastore_search_sql?sql=" + urllib.parse.quote(sql)
    d = get_json(url)
    if not d.get("success"):
        raise RuntimeError(d)
    return d["result"]["records"]


def boston_iter_year(year):
    rid = BOS_RES.get(year)
    if not rid:
        return [], 0
    where = ("lower(case_title) LIKE '%rodent%' OR lower(type) LIKE '%rodent%'")
    out, nocoord = [], 0
    offset = 0
    while True:
        sql = (f'SELECT case_enquiry_id, open_dt, case_title, type, latitude, longitude '
               f'FROM "{rid}" WHERE {where} ORDER BY case_enquiry_id LIMIT 20000 OFFSET {offset}')
        rows = ckan_sql(sql)
        if not rows:
            break
        for row in rows:
            d = parse_date(row.get("open_dt"))
            if d is None:
                continue
            c = coords(row.get("latitude"), row.get("longitude"))
            orig = row.get("case_title") or row.get("type") or "Rodent"
            if row.get("type") and row.get("type") != row.get("case_title"):
                orig = f"{orig} ({row.get('type')})"
            if c is None:
                nocoord += 1
                continue
            out.append((d, c[0], c[1], orig, 1))
        if len(rows) < 20000:
            break
        offset += 20000
        time.sleep(0.2)
    return out, nocoord


# ---- ArcGIS -------------------------------------------------------------
def ags_query(base, params, tries=4):
    p = dict(params)
    p["f"] = "json"
    url = base.rstrip("/") + "/query?" + urllib.parse.urlencode(p)
    return get_json(url, tries=tries)


def ags_count(base):
    d = ags_query(base, {"where": "1=1", "returnCountOnly": "true"})
    return int(d.get("count", 0))


def ags_pages(base, where, out_fields, order, page=1000, datefmt=None):
    offset = 0
    while True:
        d = ags_query(base, {
            "where": where, "outFields": out_fields, "returnGeometry": "false",
            "orderByFields": order, "resultOffset": offset, "resultRecordCount": page,
        })
        feats = d.get("features") or []
        if not feats:
            return
        for f in feats:
            yield f.get("attributes", {})
        if len(feats) < page and not d.get("exceededTransferLimit"):
            return
        offset += len(feats)
        time.sleep(0.1)


DC_LAYERS = {2010: 1, 2011: 2, 2012: 3, 2013: 4, 2014: 5, 2015: 6, 2016: 7, 2017: 8, 2018: 9,
             2019: 10, 2020: 11, 2021: 12, 2022: 14, 2023: 15, 2024: 16, 2025: 18, 2026: 21}
DC_WHERE = ("SERVICECODEDESCRIPTION IN ('Rodent Inspection and Treatment','DC Health Rodent & Vector Control')")


def dc_iter_year(year):
    lid = DC_LAYERS.get(year)
    if not lid:
        return [], 0
    base = f"https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/{lid}"
    out, nocoord = [], 0
    for a in ags_pages(base, DC_WHERE,
                       "SERVICEREQUESTID,SERVICECODEDESCRIPTION,ADDDATE,LATITUDE,LONGITUDE,WARD",
                       "OBJECTID"):
        ms = a.get("ADDDATE")
        if ms is None:
            continue
        d = dt.datetime.utcfromtimestamp(ms / 1000).date()
        c = coords(a.get("LATITUDE"), a.get("LONGITUDE"))
        orig = a.get("SERVICECODEDESCRIPTION") or "Rodent"
        if c is None:
            nocoord += 1
            continue
        out.append((d, c[0], c[1], orig, 1))
    return out, nocoord


BALT_WHERE = ("SRType IN ('SW-Rat Rubout','SW-Rat Rubout Follow-up',"
              "'SW-Rat Rubout Alley Concern (SW creation only)','HCD-Rodents')")
BALT_SOURCES = {
    2012: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/10", "SRRecordID"),
    2013: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/9", "SRRecordID"),
    2014: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/8", "SRRecordID"),
    2015: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/7", "SRRecordID"),
    2016: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/6", "SRRecordID"),
    2017: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/5", "SRRecordID"),
    2018: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/4", "SRRecordID"),
    2019: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/3", "SRRecordID"),
    2020: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/2", "SRRecordID"),
    2021: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/1", "SRRecordID"),
    2022: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_Yearly/FeatureServer/0", "SRRecordID"),
    2023: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_2023/FeatureServer/0", "SRRecordID"),
    2024: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_2024/FeatureServer/0", "SRRecordID"),
    2025: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_2025/FeatureServer/0", "SRRecordID"),
    2026: ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/311_Customer_Service_Requests_current/FeatureServer/0", "SRRecordID"),
}


def baltimore_iter_year(year):
    src = BALT_SOURCES.get(year)
    if not src:
        return [], 0
    base, oid = src
    out, nocoord = [], 0
    for a in ags_pages(base, BALT_WHERE, "ServiceRequestNum,SRType,CreatedDate,Latitude,Longitude,Neighborhood", oid):
        ms = a.get("CreatedDate")
        if ms is None:
            continue
        d = dt.datetime.utcfromtimestamp(ms / 1000).date()
        c = coords(a.get("Latitude"), a.get("Longitude"))
        if c is None:
            nocoord += 1
            continue
        orig = a.get("SRType") or "Rat Rubout"
        resident = 0 if "Proactive" in orig else 1
        out.append((d, c[0], c[1], orig, resident))
    return out, nocoord


DET_BASE = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/improve_detroit/FeatureServer/0"
DET_WHERE = "request_type = 'Rodent Extermination'"


def detroit_iter_year(year):
    where = f"{DET_WHERE} AND created_at >= DATE '{year}-01-01' AND created_at < DATE '{year + 1}-01-01'"
    out, nocoord = [], 0
    for a in ags_pages(DET_BASE, where, "issue_id,request_type,created_at,latitude,longitude,neighborhood", "ObjectId"):
        ms = a.get("created_at")
        if ms is None:
            continue
        d = dt.datetime.utcfromtimestamp(ms / 1000).date()
        c = coords(a.get("latitude"), a.get("longitude"))
        if c is None:
            nocoord += 1
            continue
        out.append((d, c[0], c[1], a.get("request_type") or "Rodent Extermination", 1))
    return out, nocoord


# ---- Pittsburgh (WPRDC CKAN) -------------------------------------------
PIT_RES = "5202679a-d243-402e-b82a-63189995a942"


def pgh_iter_year(year):
    out, nocoord = [], 0
    offset = 0
    while True:
        sql = (f'SELECT case_number, subject, created_date_et, latitude, longitude, neighborhood '
               f'FROM "{PIT_RES}" WHERE subject = \'Rodent Control\' '
               f"AND created_date_et >= '{year}-01-01' AND created_date_et < '{year + 1}-01-01' "
               f'ORDER BY case_number LIMIT 20000 OFFSET {offset}')
        url = "https://data.wprdc.org/api/3/action/datastore_search_sql?sql=" + urllib.parse.quote(sql)
        d = get_json(url)
        rows = d["result"]["records"] if d.get("success") else []
        if not rows:
            break
        for row in rows:
            d0 = parse_date(row.get("created_date_et"))
            if d0 is None:
                continue
            c = coords(row.get("latitude"), row.get("longitude"))
            if c is None:
                nocoord += 1
                continue
            out.append((d0, c[0], c[1], row.get("subject") or "Rodent Control", 1))
        if len(rows) < 20000:
            break
        offset += 20000
        time.sleep(0.2)
    return out, nocoord


# ---- registry -----------------------------------------------------------
def build_city_specs():
    return [
        {
            "slug": "nyc", "city": "New York City", "state": "NY", "short": "NYC",
            "source_name": "NYC Open Data - 311 Service Requests",
            "source_url": "https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9",
            "dataset_ids": "erm2-nwe9 (2020-present), 76ig-c548 (2010-2019)",
            "filter": "complaint_type = 'Rodent'",
            "definition": "Every 311 service request filed under complaint type Rodent (rat sightings, mouse sightings, signs of rodent activity, rodent bites). Resident reports, not confirmed infestations.",
            "fields": "created_date, complaint_type, descriptor, latitude, longitude, unique_key",
            "license": "NYC Open Data terms of use (public domain-style, attribution requested)",
            "types": ["Rodent complaint", "Rodent / Rat Sighting", "Rodent / Mouse Sighting",
                      "Rodent / Signs of Rodent Activity", "Rodent / Rat Bite", "Rodent / Rodent Bite",
                      "Rodent / Unsanitary Animal Pvt Property", "Rodent / Condition Attracting Rodents"],
            "iter": nyc_iter_year,
        },
        {
            "slug": "chicago", "city": "Chicago", "state": "IL", "short": "Chicago",
            "source_name": "Chicago Data Portal - 311 Service Requests",
            "source_url": "https://data.cityofchicago.org/Service-Requests/311-Service-Requests/v6vf-nfxy",
            "dataset_ids": "v6vf-nfxy (2019-present), 97t6-zrhs (Rodent Baiting, historical)",
            "filter": "sr_type = 'Rodent Baiting/Rat Complaint' AND duplicate = false; historical: type_of_service_request = 'Rodent Baiting/Rat Complaint'",
            "definition": "311 requests to bait a location for rats. Duplicate-flagged requests are excluded (v6vf-nfxy). The historical Rodent Baiting dataset covers requests before the 2019 dataset migration.",
            "fields": "created_date, sr_type, latitude, longitude, sr_number (historical: creation_date, type_of_service_request)",
            "license": "Chicago Data Portal terms of use (public data)",
            "types": ["Rodent Baiting/Rat Complaint"],
            "iter": chicago_iter_year,
        },
        {
            "slug": "boston", "city": "Boston", "state": "MA", "short": "Boston",
            "source_name": "Analyze Boston - 311 Service Requests",
            "source_url": "https://data.boston.gov/dataset/311-service-requests",
            "dataset_ids": "311 Service Requests, one CKAN resource per year",
            "filter": "lower(case_title) LIKE '%rodent%' OR lower(type) LIKE '%rodent%'",
            "definition": "Boston 311 cases opened for rodent activity (Inspectional Services Department) and related rodent case types.",
            "fields": "case_enquiry_id, open_dt, case_title, type, latitude, longitude, neighborhood",
            "license": "Analyze Boston open data license (CC BY 4.0 style, attribution)",
            "types": ["Rodent Activity", "Rodent Control", "Rodent complaint"],
            "iter": boston_iter_year,
        },
        {
            "slug": "washington-dc", "city": "Washington", "state": "DC", "short": "Washington DC",
            "source_name": "Open Data DC - 311 City Service Requests",
            "source_url": "https://opendata.dc.gov/datasets/DCGIS::311-city-service-requests-in-2025",
            "dataset_ids": "DCGIS_DATA/ServiceRequests (one layer per year, 2010-2026)",
            "filter": "SERVICECODEDESCRIPTION IN ('Rodent Inspection and Treatment','DC Health Rodent & Vector Control')",
            "definition": "311 requests DC Health opens to inspect and bait a property for rats. The service code was renamed during 2026, so both codes are counted.",
            "fields": "SERVICEREQUESTID, SERVICECODEDESCRIPTION, ADDDATE, LATITUDE, LONGITUDE, WARD",
            "license": "Open Data DC terms of use",
            "types": ["Rodent Inspection and Treatment", "DC Health Rodent & Vector Control"],
            "iter": dc_iter_year,
        },
        {
            "slug": "baltimore", "city": "Baltimore", "state": "MD", "short": "Baltimore",
            "source_name": "Open Baltimore - 311 Customer Service Requests",
            "source_url": "https://data.baltimorecity.gov/datasets/311-customer-service-requests",
            "dataset_ids": "311_Customer_Service_Requests_Yearly (2010-2022) + yearly services 2023-2026",
            "filter": "SRType IN ('SW-Rat Rubout','SW-Rat Rubout Follow-up','SW-Rat Rubout Alley Concern (SW creation only)','HCD-Rodents')",
            "definition": "Resident-initiated rat removal requests (SW-Rat Rubout and follow-ups) and Housing's HCD-Rodents requests. DPW's own scheduled baiting runs (SW-Rat Rubout Proactive, ~95% of all rodent records in this dataset) are excluded, because counting the city's work calendar as rodent complaints would distort every comparison.",
            "fields": "ServiceRequestNum, SRType, CreatedDate, Latitude, Longitude, Neighborhood",
            "license": "Open Baltimore terms of use",
            "types": ["SW-Rat Rubout", "SW-Rat Rubout Follow-up", "SW-Rat Rubout Alley Concern (SW creation only)",
                      "HCD-Rodents"],
            "iter": baltimore_iter_year,
        },
        {
            "slug": "detroit", "city": "Detroit", "state": "MI", "short": "Detroit",
            "source_name": "City of Detroit Open Data - Improve Detroit Issues",
            "source_url": "https://data.detroitmi.gov/datasets/improve-detroit-issues",
            "dataset_ids": "improve_detroit (ArcGIS FeatureServer)",
            "filter": "request_type = 'Rodent Extermination'",
            "definition": "Improve Detroit requests asking the city to treat a property for rats or mice.",
            "fields": "issue_id, request_type, created_at, latitude, longitude, neighborhood",
            "license": "City of Detroit open data terms",
            "types": ["Rodent Extermination"],
            "iter": detroit_iter_year,
        },
        {
            "slug": "cincinnati", "city": "Cincinnati", "state": "OH", "short": "Cincinnati",
            "source_name": "City of Cincinnati Open Data - 311 (Non-Emergency) Service Requests",
            "source_url": "https://data.cincinnati-oh.gov/resource/gcej-gmiw",
            "dataset_ids": "gcej-gmiw",
            "filter": "upper(sr_type_desc) LIKE '%RATS%' OR upper(sr_type_desc) LIKE '%RODENT%'",
            "definition": "Cincinnati 311 rodent service types: rats in or around a building, rat problems/infestations, rats in sewers, and food-establishment rodent violations.",
            "fields": "sr_number, sr_type_desc, date_created, latitude, longitude, neighborhood",
            "license": "City of Cincinnati open data terms",
            "types": ["RATS, IN A BUILDING", "RATS, OUTSIDE A BUILDING", "RATS, PROBLEM/INFESTATION",
                      "RATS, IN OR AROUND A BUILDING", "RATS IN SEWER, REM REQ", "INSTITUTION, RATS IN  BLDG",
                      "FOOD OPERATION, RODENTS"],
            "iter": cincy_iter_year,
        },
        {
            "slug": "pittsburgh", "city": "Pittsburgh", "state": "PA", "short": "Pittsburgh",
            "source_name": "Western Pennsylvania Regional Data Center - 311 Data",
            "source_url": "https://data.wprdc.org/dataset/pittsburgh-311-data",
            "dataset_ids": "311 Data (resource 5202679a-d243-402e-b82a-63189995a942)",
            "filter": "subject = 'Rodent Control'",
            "definition": "Pittsburgh 311 requests filed under the Rodent Control subject.",
            "fields": "case_number, subject, created_date_et, latitude, longitude, neighborhood",
            "license": "WPRDC terms (CC BY 4.0 for this dataset)",
            "types": ["Rodent Control"],
            "iter": pgh_iter_year,
        },
        {
            "slug": "cambridge", "city": "Cambridge", "state": "MA", "short": "Cambridge",
            "source_name": "Cambridge Open Data - Commonwealth Connect Service Requests",
            "source_url": "https://data.cambridgema.gov/resource/2z9k-mv9g",
            "dataset_ids": "2z9k-mv9g",
            "filter": "issue_type LIKE '%rodent%' or the issue type contains a standalone rat/rodent word (post-filter)",
            "definition": "Cambridge Commonwealth Connect requests about rodent sightings, dead rodents, and rat harborage conditions.",
            "fields": "ticket_id, issue_type, ticket_created_date_time, lat, lng, address",
            "license": "Cambridge Open Data terms",
            "types": ["Rodent Sighting", "Dead rat", "Dead Rodent", "Rat", "Rat holes", "Rodent complaint (other)"],
            "iter": cambridge_iter_year,
        },
        {
            "slug": "san-francisco", "city": "San Francisco", "state": "CA", "short": "San Francisco",
            "source_name": "DataSF - 311 Cases",
            "source_url": "https://data.sfgov.org/City-Infrastructure/311-Cases/vw6y-z8j6",
            "dataset_ids": "vw6y-z8j6",
            "filter": "service_details = 'Infestation_Rodent_Insect'",
            "definition": "San Francisco 311 cases whose service detail is Infestation_Rodent_Insect (rodent or insect infestation reported in a building), handled by the Department of Public Health's vector control programme.",
            "fields": "service_request_id, requested_datetime, service_name, service_subtype, service_details, lat, long",
            "license": "DataSF open data terms",
            "types": ["Infestation_Rodent_Insect"],
            "iter": sf_iter_year,
        },
        {
            "slug": "new-orleans", "city": "New Orleans", "state": "LA", "short": "New Orleans",
            "source_name": "Open Data NOLA - 311 Calls",
            "source_url": "https://data.nola.gov/resource/2jgv-pqrq",
            "dataset_ids": "2jgv-pqrq (311 OPCD Calls, 2012-present)",
            "filter": "request_type = 'Mosquito, Termite & Rodent Control' AND request_reason IN ('Rodent Complaint (Mice & Rats)','Rodent Complaint (Rats)')",
            "definition": "New Orleans 311 calls to the Mosquito, Termite & Rodent Control Board specifically about rats or mice. Mosquito/termite calls in the same request type, and the board's explicit 'Non-Rodent Complaint' reasons, are excluded.",
            "fields": "service_request, request_type, request_reason, date_created, latitude, longitude, address_councildis",
            "license": "Open Data NOLA terms of use",
            "types": ["Rodent Complaint (Rats)", "Rodent Complaint (Mice & Rats)"],
            "iter": nola_iter_year,
        },
        {
            "slug": "baton-rouge", "city": "Baton Rouge", "state": "LA", "short": "Baton Rouge",
            "source_name": "Open Data BR - Mosquito and Rodent Service Requests",
            "source_url": "https://data.brla.gov/resource/bktv-u9ua",
            "dataset_ids": "bktv-u9ua",
            "filter": "type IN ('RODENT','BOTH')",
            "definition": "Baton Rouge mosquito and rodent control service requests. 'BOTH' records are requests that cover mosquitoes and rodents.",
            "fields": "recordno, type, call_in_date, address, city_name, geolocation, called_in",
            "license": "Open Data BR terms",
            "types": ["RODENT", "BOTH (mosquito + rodent)"],
            "iter": brla_iter_year,
        },
    ]


# NYC adapter needs descriptor handling -> defined after helpers
def nyc_iter_year(year):
    dataset = ("data.cityofnewyork.us", "76ig-c548") if year <= 2019 else ("data.cityofnewyork.us", "erm2-nwe9")
    return make_socrata_rows_adapter(dataset, "created_date", "complaint_type", "descriptor",
                                     "complaint_type='Rodent'", ("latitude", "longitude"), "unique_key")(year)


def chicago_iter_year(year):
    if year <= 2018:
        dataset = ("data.cityofchicago.org", "97t6-zrhs")
        typef, datef = "type_of_service_request", "creation_date"
        where = f"{typef} = 'Rodent Baiting/Rat Complaint'"
        return make_socrata_rows_adapter(dataset, datef, typef, None, where, ("latitude", "longitude"),
                                          "service_request_number")(year)
    dataset = ("data.cityofchicago.org", "v6vf-nfxy")
    where = "sr_type = 'Rodent Baiting/Rat Complaint' AND duplicate = false"
    return make_socrata_rows_adapter(dataset, "created_date", "sr_type", None, where, ("latitude", "longitude"),
                                      "sr_number")(year)


RAT_WORD = None


def cambridge_iter_year(year):
    import re
    global RAT_WORD
    if RAT_WORD is None:
        RAT_WORD = re.compile(r"\b(rats?|rodents?)\b", re.I)
    dataset = ("data.cambridgema.gov", "2z9k-mv9g")
    where = ("(upper(issue_type) LIKE '%RODENT%' OR upper(issue_type) LIKE 'RAT%' "
             "OR upper(issue_type) LIKE '% RAT%' OR upper(issue_type) LIKE '%RAT %')")
    out, nocoord = [], 0
    select = "ticket_id,issue_type,ticket_created_date_time,lat,lng,address"
    rows = socrata_pages(dataset, select, year_where("ticket_created_date_time", year, where))
    for row in rows:
        it = row.get("issue_type") or ""
        if not RAT_WORD.search(it):
            continue
        d = parse_date(row.get("ticket_created_date_time"))
        if d is None:
            continue
        c = coords(row.get("lat"), row.get("lng"))
        if c is None:
            nocoord += 1
            continue
        out.append((d, c[0], c[1], it, 1))
    return out, nocoord


def brla_iter_year(year):
    dataset = ("data.brla.gov", "bktv-u9ua")
    where = "type IN ('RODENT','BOTH')"
    out, nocoord = [], 0
    select = "recordno,type,call_in_date,address,city_name,geolocation,called_in"
    for row in socrata_pages(dataset, select, year_where("call_in_date", year, where), order="recordno"):
        d = parse_date(row.get("call_in_date"))
        if d is None:
            continue
        geo = row.get("geolocation") or {}
        c = None
        if isinstance(geo, dict):
            cc = geo.get("coordinates") or []
            if len(cc) == 2:
                c = coords(cc[1], cc[0])
        if c is None:
            nocoord += 1
            continue
        label = "RODENT" if row.get("type") == "RODENT" else "BOTH (mosquito + rodent)"
        out.append((d, c[0], c[1], label, 1))
    return out, nocoord


def cincy_iter_year(year):
    dataset = ("data.cincinnati-oh.gov", "gcej-gmiw")
    where = "(upper(sr_type_desc) LIKE '%RATS%' OR upper(sr_type_desc) LIKE '%RODENT%')"
    select = "sr_number,sr_type_desc,date_created,latitude,longitude,neighborhood"
    out, nocoord = [], 0
    for row in socrata_pages(dataset, select, year_where("date_created", year, where), order="sr_number"):
        d = parse_date(row.get("date_created"))
        if d is None:
            continue
        c = coords(row.get("latitude"), row.get("longitude"))
        if c is None:
            nocoord += 1
            continue
        out.append((d, c[0], c[1], (row.get("sr_type_desc") or "RATS").strip(), 1))
    return out, nocoord


def sf_iter_year(year):
    dataset = ("data.sfgov.org", "vw6y-z8j6")
    where = "service_details = 'Infestation_Rodent_Insect'"
    select = "service_request_id,requested_datetime,service_name,service_subtype,service_details,lat,long,analysis_neighborhood"
    out, nocoord = [], 0
    for row in socrata_pages(dataset, select, year_where("requested_datetime", year, where), order="service_request_id"):
        d = parse_date(row.get("requested_datetime"))
        if d is None:
            continue
        c = coords(row.get("lat"), row.get("long"))
        if c is None:
            nocoord += 1
            continue
        out.append((d, c[0], c[1], "Infestation_Rodent_Insect", 1))
    return out, nocoord


NOLA_WHERE = ("request_type = 'Mosquito, Termite & Rodent Control' AND "
              "request_reason IN ('Rodent Complaint (Mice & Rats)','Rodent Complaint (Rats)')")


def nola_iter_year(year):
    dataset = ("data.nola.gov", "2jgv-pqrq")
    select = "service_request,request_type,request_reason,date_created,latitude,longitude,address_councildis"
    out, nocoord = [], 0
    for row in socrata_pages(dataset, select, year_where("date_created", year, NOLA_WHERE), order="service_request"):
        d = parse_date(row.get("date_created"))
        if d is None:
            continue
        c = coords(row.get("latitude"), row.get("longitude"))
        if c is None:
            nocoord += 1
            continue
        label = row.get("request_reason") or "Rodent Complaint"
        out.append((d, c[0], c[1], label, 1))
    return out, nocoord


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"cities": {}}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=1, sort_keys=True)


def write_city_year(slug, year, records):
    d = os.path.join(DATA, slug)
    os.makedirs(d, exist_ok=True)
    rows = [[day_index(r[0]), r[1], r[2], r[3], r[4]] for r in records]
    rows.sort(key=lambda x: x[0])
    payload = {"year": year, "n": len(rows), "rows": rows}
    path = os.path.join(d, f"{year}.json")
    with open(path, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", nargs="*", default=None)
    ap.add_argument("--min-year", type=int, default=MIN_YEAR_DEFAULT)
    ap.add_argument("--max-year", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only-current-year", action="store_true")
    ap.add_argument("--manifest-only", action="store_true")
    args = ap.parse_args()

    today = dt.date.today()
    max_year = args.max_year or today.year
    state = load_state()
    specs = build_city_specs()
    if args.manifest_only:
        build_manifest(state, specs)
        return
    if args.city:
        specs = [s for s in specs if s["slug"] in args.city]

    for spec in specs:
        slug = spec["slug"]
        cstate = state["cities"].setdefault(slug, {"years": {}})
        types_list = list(spec["types"])
        for year in range(args.min_year, max_year + 1):
            is_current = year == max_year
            if args.only_current_year and not is_current:
                continue
            existing = cstate["years"].get(str(year))
            if existing and not args.force and not is_current:
                log(f"[skip] {slug} {year} ({existing['n']} rows)")
                continue
            t0 = time.time()
            try:
                records, nocoord = spec["iter"](year)
            except Exception as e:  # noqa: BLE001 - keep other cities going
                log(f"[fail] {slug} {year}: {e}")
                continue
            # normalise original classifications into the city's type list
            idx = {t: i for i, t in enumerate(types_list)}
            norm = []
            for r in records:
                label = r[3]
                if label not in idx:
                    idx[label] = len(types_list)
                    types_list.append(label)
                norm.append((r[0], r[1], r[2], idx[label], r[4]))
            n = write_city_year(slug, year, norm) if norm else write_city_year(slug, year, [])
            cstate["years"][str(year)] = {"n": n, "nocoord": nocoord, "fetched": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"}
            log(f"[ok] {slug} {year}: {n} rows, {nocoord} without coordinates, {time.time() - t0:.1f}s")
            state["cities"][slug]["types"] = types_list
            save_state(state)
        state["cities"][slug]["types"] = types_list
        save_state(state)

    build_manifest(state, build_city_specs())


def build_manifest(state, specs):
    manifest = {"generated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "cities": []}
    total = 0
    for spec in specs:
        slug = spec["slug"]
        cstate = state["cities"].get(slug, {"years": {}})
        years = {int(y): v for y, v in cstate.get("years", {}).items() if v.get("n") is not None}
        n_total = sum(v["n"] for v in years.values())
        nocoord = sum(v.get("nocoord", 0) for v in years.values())
        dates = []
        for y in years:
            path = os.path.join(DATA, slug, f"{y}.json")
            if not os.path.exists(path):
                continue
            with open(path) as f:
                payload = json.load(f)
            if payload["rows"]:
                dates.append((payload["rows"][0][0], payload["rows"][-1][0]))
        # exact min/max days from first/last of each sorted year
        dmin = min((d[0] for d in dates), default=None)
        dmax = max((d[1] for d in dates), default=None)
        iso = lambda d: (EPOCH + dt.timedelta(days=d)).isoformat() if d is not None else None
        entry = {
            "slug": slug, "city": spec["city"], "state": spec["state"], "short": spec["short"],
            "source_name": spec["source_name"], "source_url": spec["source_url"],
            "dataset_ids": spec["dataset_ids"], "filter": spec["filter"], "definition": spec["definition"],
            "fields": spec["fields"], "license": spec["license"],
            "types": cstate.get("types", spec["types"]),
            "years": {str(y): years[y]["n"] for y in sorted(years)},
            "nocoord": nocoord,
            "n": n_total,
            "date_min": iso(dmin), "date_max": iso(dmax),
            "year_min": min(years) if years else None, "year_max": max(years) if years else None,
        }
        total += n_total
        manifest["cities"].append(entry)
    manifest["total_records"] = total
    manifest["total_nocoord"] = sum(c["nocoord"] for c in manifest["cities"])
    with open(os.path.join(DATA, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    log(f"[manifest] {len(manifest['cities'])} cities, {total} geolocated records")
    for c in manifest["cities"]:
        log(f"   {c['slug']:14s} {c['n']:>7d} rows  {c['date_min']}..{c['date_max']}  nocoord={c['nocoord']}")


if __name__ == "__main__":
    main()
