# scripts/fetch_overpass_poi.py (v3)
import os, json, time, requests
from osm2geojson import json2geojson

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OPQ  = os.path.join(BASE, "scripts", "overpass")
os.makedirs(DATA, exist_ok=True)

ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]
HEADERS = {"User-Agent":"cevennes-map/1.0","Accept":"application/json","Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"}

def run_query(ql: str, tries_per_endpoint: int = 2, backoff: float = 2.5):
    last_err = None
    for url in ENDPOINTS:
        for attempt in range(1, tries_per_endpoint + 1):
            try:
                r = requests.post(url, data={"data": ql}, headers=HEADERS, timeout=180)
                if r.ok:
                    return r.json()
                if r.status_code in (400,403):
                    r2 = requests.get(url, params={"data": ql}, headers=HEADERS, timeout=180)
                    if r2.ok:
                        return r2.json()
                time.sleep(backoff * attempt)
            except Exception as e:
                last_err = e; time.sleep(backoff * attempt)
    raise SystemExit(f"Overpass indisponible: {last_err}")

def save_geojson(name: str, osm_json: dict):
    gj = json2geojson(osm_json)
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, indent=2)
    print("✓", name)

def graceful_empty(name: str, reason: str):
    empty = {"type":"FeatureCollection","features":[]}
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(empty, f, ensure_ascii=False, indent=2)
    print(f"⚠ {name} vide ({reason})")

def fetch_from_file(ql_filename: str, out_name: str):
    path = os.path.join(OPQ, ql_filename)
    if not os.path.isfile(path):
        print(f"⏭ Requête absente: {ql_filename}"); return
    raw = open(path, "rb").read().decode("utf-8-sig").replace("\r","")
    ql  = raw.strip() + "\n"
    try:
        save_geojson(out_name, run_query(ql))
    except SystemExit as e:
        graceful_empty(out_name, str(e))

def main():
    fetch_from_file("gr.ql", "sentiers_gr.geojson")
    mapping = {
        "villes":"poi_villes.geojson","villages":"poi_villages.geojson","towns":"poi_towns.geojson","hameaux":"poi_hameaux.geojson",
        "offices_tourisme":"poi_offices_tourisme.geojson","cols_sommets":"poi_cols_sommets.geojson","cascades":"poi_cascades.geojson",
        "panoramas":"poi_panoramas.geojson","sites_historiques":"poi_sites_historiques.geojson","sites_naturels":"poi_sites_naturels.geojson",
        "lieux_insolites":"poi_lieux_insolites.geojson","activites":"poi_activites.geojson","commerces":"poi_commerces.geojson",
    }
    for key, outname in mapping.items():
        fetch_from_file(f"{key}.ql", outname); time.sleep(0.8)

if __name__ == "__main__":
    main()
