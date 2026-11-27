# Data sources

Everything in `data/` comes from a public municipal 311 API. No record is synthetic, modelled,
estimated, or hand-entered. This file records the exact endpoint, filter and field mapping for each
city, plus the cities that were checked and excluded and why.

Fetched by [`scripts/fetch_311.py`](../scripts/fetch_311.py). Last full refresh: 2026‑11‑27.
**12 cities · 1,522,914 geolocated records · 5,286 fetched records without coordinates.**

---

## Included cities

### New York City, NY — 470,796 records
- **Datasets**: `erm2-nwe9` (311 Service Requests from 2020 to Present) and `76ig-c548` (2010–2019).
- **Endpoint**: `https://data.cityofnewyork.us/resource/erm2-nwe9.json` (Socrata SODA 2.1).
- **Filter**: `complaint_type = 'Rodent'`.
- **Fields used**: `created_date`, `complaint_type`, `descriptor`, `latitude`, `longitude`, `unique_key`.
- **What it counts**: resident-filed 311 requests under complaint type *Rodent* — rat sightings,
  mouse sightings, signs of rodent activity, rodent bites. Descriptors are preserved as
  `Rodent / Rat Sighting` etc.
- **Licence**: NYC Open Data terms of use (public data, attribution requested).
- **Notes**: 3,143 fetched records had no coordinates and are excluded.

### Chicago, IL — 660,773 records
- **Datasets**: `v6vf-nfxy` (311 Service Requests, 2019→) and `97t6-zrhs` (311 Service Requests —
  Rodent Baiting, historical, 1999–2018).
- **Endpoint**: `https://data.cityofchicago.org/resource/v6vf-nfxy.json`.
- **Filter**: `sr_type = 'Rodent Baiting/Rat Complaint' AND duplicate = false`; historical dataset
  filtered on `type_of_service_request = 'Rodent Baiting/Rat Complaint'`.
- **Fields**: `created_date` / `creation_date`, `sr_type` / `type_of_service_request`,
  `latitude`, `longitude`, `sr_number` / `service_request_number`.
- **What it counts**: requests asking the city to bait a location for rats.
- **Licence**: Chicago Data Portal terms of use.
- **Notes**: the `duplicate` flag only exists in the post-2019 dataset; the historical dataset has
  no such flag.

### Washington, DC — 129,708 records
- **Dataset**: `DCGIS_DATA/ServiceRequests` (311 City Service Requests), one map layer per year.
- **Endpoint**: `https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/<layer>`
  (layers 1–16, 18, 21 for 2010–2026), queried through ArcGIS REST with `resultOffset` paging.
- **Filter**: `SERVICECODEDESCRIPTION IN ('Rodent Inspection and Treatment','DC Health Rodent & Vector Control')`.
- **Fields**: `SERVICEREQUESTID`, `SERVICECODEDESCRIPTION`, `ADDDATE`, `LATITUDE`, `LONGITUDE`, `WARD`.
- **What it counts**: requests DC Health opens to inspect and bait a property for rats. The service
  code was renamed during 2026, so both codes are counted to keep the series continuous.
- **Licence**: Open Data DC terms of use.
- **Notes**: coverage begins 2013‑05‑23; the 2012 layer contains no rodent-coded requests.

### Baltimore, MD — 125,686 records
- **Datasets**: `311_Customer_Service_Requests_Yearly` (layers for 2010–2022) plus the yearly
  services `311_Customer_Service_Requests_2023`, `…_2024`, `…_2025`, `…_current` (2026).
- **Endpoint**: ArcGIS REST on `services1.arcgis.com/UWYHeuuJISiGmgXx`.
- **Filter**: `SRType IN ('SW-Rat Rubout','SW-Rat Rubout Follow-up','SW-Rat Rubout Alley Concern (SW creation only)','HCD-Rodents')`.
- **Fields**: `ServiceRequestNum`, `SRType`, `CreatedDate`, `Latitude`, `Longitude`, `Neighborhood`.
- **What it counts**: resident-initiated rat-removal requests, follow-up requests, alley concerns,
  and Housing's `HCD-Rodents` requests.
- **Licence**: Open Baltimore terms of use.
- **Notes**: `SW-Rat Rubout Proactive` (DPW's own scheduled baiting runs, roughly 95% of the rodent
  rows in this dataset — 123,755 rows in 2025 alone) is **excluded**: it is a work calendar, not
  resident reporting. Including it would make Baltimore look 20× busier than comparable cities.

### Boston, MA — 47,734 records
- **Dataset**: `311-service-requests` on Analyze Boston (CKAN), one resource per year.
- **Endpoint**: `https://data.boston.gov/api/3/action/datastore_search_sql`.
- **Filter**: `lower(case_title) LIKE '%rodent%' OR lower(type) LIKE '%rodent%'`.
- **Fields**: `case_enquiry_id`, `open_dt`, `case_title`, `type`, `latitude`, `longitude`,
  `neighborhood`.
- **What it counts**: Inspectional Services rodent cases (“Rodent Activity”) and related rodent
  case types.
- **Licence**: Analyze Boston open data licence.
- **Notes**: the 2014 resource exists but contains zero rows in Analyze Boston's datastore, so 2014
  is missing for Boston. 441 fetched records lacked coordinates.

### Baton Rouge, LA — 34,057 records
- **Dataset**: `bktv-u9ua` — Mosquito and Rodent Service Requests (East Baton Rouge Parish).
- **Endpoint**: `https://data.brla.gov/resource/bktv-u9ua.json`.
- **Filter**: `type IN ('RODENT','BOTH')`.
- **Fields**: `recordno`, `type`, `call_in_date`, `address`, `city_name`, `geolocation`, `called_in`.
- **What it counts**: rodent-control service requests; `BOTH` records cover mosquito *and* rodent
  calls, and are kept as their own original classification.
- **Licence**: Open Data BR terms of use.
- **Notes**: coverage starts 2019‑02‑07.

### Detroit, MI — 27,177 records
- **Dataset**: `improve_detroit` (Improve Detroit Issues).
- **Endpoint**: `https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/improve_detroit/FeatureServer/0`.
- **Filter**: `request_type = 'Rodent Extermination'` (+ `created_at` year window).
- **Fields**: `issue_id`, `request_type`, `created_at`, `latitude`, `longitude`, `neighborhood`.
- **What it counts**: resident requests for the city to treat a property for rats or mice.
- **Licence**: City of Detroit open data terms.
- **Notes**: coverage starts 2017‑06‑14.

### Pittsburgh, PA — 8,384 records
- **Dataset**: Pittsburgh 311 Data (resource `5202679a-d243-402e-b82a-63189995a942`) on the
  Western Pennsylvania Regional Data Center (CKAN).
- **Endpoint**: `https://data.wprdc.org/api/3/action/datastore_search_sql`.
- **Filter**: `subject = 'Rodent Control'`.
- **Fields**: `case_number`, `subject`, `created_date_et`, `latitude`, `longitude`, `neighborhood`.
- **Licence**: WPRDC terms; this dataset is published as CC BY 4.0.
- **Notes**: coverage starts 2015‑04‑30.

### Cambridge, MA — 5,312 records
- **Dataset**: `2z9k-mv9g` — Commonwealth Connect Service Requests.
- **Endpoint**: `https://data.cambridgema.gov/resource/2z9k-mv9g.json`.
- **Filter**: `issue_type` containing a standalone rat/rodent word (`RODENT%`, `RAT%`, `% RAT%`,
  `%RAT %`) then a word-boundary post-filter, because a naive `LIKE '%RAT%'` also matches
  “Ope**rat**ions”.
- **Fields**: `ticket_id`, `issue_type`, `ticket_created_date_time`, `lat`, `lng`, `address`.
- **What it counts**: rodent sightings, dead-rodent reports, rat harborage complaints.
- **Licence**: Cambridge Open Data terms.

### San Francisco, CA — 2,734 records
- **Dataset**: `vw6y-z8j6` — 311 Cases.
- **Endpoint**: `https://data.sfgov.org/resource/vw6y-z8j6.json`.
- **Filter**: `service_details = 'Infestation_Rodent_Insect'`.
- **Fields**: `service_request_id`, `requested_datetime`, `service_name`, `service_subtype`,
  `service_details`, `lat`, `long`, `analysis_neighborhood`.
- **What it counts**: 311 cases whose service detail is a rodent/insect infestation reported in a
  building; they are routed to the Department of Public Health's vector-control programme.
- **Licence**: DataSF open data terms.
- **Notes**: 1,077 of 3,811 fetched SF records have no coordinates (28%) and are excluded — the
  highest missing rate in the atlas. The dataset's rodent detail also goes quiet after 2024‑02‑28,
  which is why San Francisco's series ends there rather than at the current month.

### New Orleans, LA — 6,497 records
- **Dataset**: `2jgv-pqrq` — 311 OPCD Calls (2012–present).
- **Endpoint**: `https://data.nola.gov/resource/2jgv-pqrq.json`.
- **Filter**: `request_type = 'Mosquito, Termite & Rodent Control' AND request_reason IN ('Rodent Complaint (Mice & Rats)','Rodent Complaint (Rats)')`.
- **Fields**: `service_request`, `request_type`, `request_reason`, `date_created`, `latitude`,
  `longitude`, `address_councildis`.
- **What it counts**: calls to the Mosquito, Termite & Rodent Control Board specifically about rats
  or mice. Mosquito and termite calls in the same request type — and the board's explicit
  “Non-Rodent Complaint (Mice, Possums, Snakes)” reasons — are excluded.
- **Licence**: Open Data NOLA terms of use.
- **Notes**: coverage starts 2019‑01‑01.

### Cincinnati, OH — 4,056 records
- **Dataset**: `gcej-gmiw` — Cincinnati 311 (Non-Emergency) Service Requests.
- **Endpoint**: `https://data.cincinnati-oh.gov/resource/gcej-gmiw.json`.
- **Filter**: `upper(sr_type_desc) LIKE '%RATS%' OR upper(sr_type_desc) LIKE '%RODENT%'`.
- **Fields**: `sr_number`, `sr_type_desc`, `date_created`, `latitude`, `longitude`, `neighborhood`.
- **What it counts**: rats in or around a building, rat problems/infestations, rats in sewers,
  institutional infestations and food-establishment rodent violations.
- **Licence**: City of Cincinnati open data terms.

---

## Checked and excluded

These portals were queried directly during research (November 2026). Each was excluded because it
publishes **no rodent-specific 311 category**, or publishes one **without coordinates** — not
because the data was inconvenient.

| City | Dataset checked | Result |
|---|---|---|
| Seattle, WA | `data.seattle.gov/5ngg-rpne` (Customer Service Requests) | All 47 request types enumerated; none is rat/rodent related (closest: “Dead Animal”, “General Inquiry – Animal Shelter”). Rats are handled by Public Health – Seattle & King County, outside 311. |
| Los Angeles, CA | `data.lacity.org/rq3b-xjk8` (MyLA311) | 12 request types; no rodent category (closest: “Dead Animal Removal”). |
| Philadelphia, PA | `phl.carto.com` `public_cases_fc` | 40+ service names checked; no rodent category. |
| Dallas, TX | `dallasopendata.com/4n3h-rfqm` | No rodent service request type. |
| Nashville, TN | `hubNashville` 311 ArcGIS service | 205 distinct `Request_Type` values; none rodent related. |
| Louisville, KY | Metro 311 ArcGIS services | 55 distinct service names; none rodent related. |
| Houston, TX | Houston 311 ArcGIS service | 132 distinct `CASE_TYPE` values; none rodent related. |
| Kansas City, MO | `data.kcmo.org` 311 datasets | Per-record 311 data is aggregated by issue type only; no geocoded individual rodent requests. |
| Norfolk, VA | `data.norfolk.gov/nbyu-xjez` | Has “Rat Observed” (1,278) and “Potential Rat Harborage” (734) — but no coordinates in the dataset. |
| Somerville, MA | `data.somervillema.gov/4pyi-uqq6` | Has “Rats” (8,824) and a Rodent Assistance Program — but no coordinates in the dataset. |
| Montgomery County, MD | `data.montgomerycountymd.gov/xspi-x2bx` | MC311 service requests; rodent not a distinct published category with coordinates. |

Adding any of these later is a self-contained change: one adapter in `scripts/fetch_311.py`, one
entry in `build_city_specs()`, and a re-run.

---

## Attribution and licence summary

| City | Data owner | Terms |
|---|---|---|
| New York | NYC Department of Information Technology & Telecommunications | NYC Open Data Terms of Use |
| Chicago | City of Chicago | Chicago Data Portal Terms of Use |
| Washington | DC Office of the Chief Technology Officer | Open Data DC Terms of Use |
| Baltimore | Baltimore City | Open Baltimore Terms of Use |
| Boston | City of Boston | Analyze Boston Open Data Policy |
| Baton Rouge | City of Baton Rouge / EBR Parish | Open Data BR Terms of Use |
| Detroit | City of Detroit | Detroit Open Data Terms of Use |
| Pittsburgh | City of Pittsburgh / WPRDC | CC BY 4.0 |
| Cambridge | City of Cambridge | Cambridge Open Data Terms of Use |
| San Francisco | City & County of San Francisco | DataSF Open Data Terms of Use |
| New Orleans | City of New Orleans | Open Data NOLA Terms of Use |
| Cincinnati | City of Cincinnati | Cincinnati Open Data Terms of Use |

Redistribution here is under each city's own open-data terms; the code is MIT.
