import requests
import urllib3
import pandas as pd
from datetime import date
import time
import os
import argparse
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.meteo.lt/v1"
REQUESTS_PER_MINUTE = 170 # the API allows a maximum of 180 requests/minute

rate_lock = threading.Lock()
request_timestamps = deque()

stations = [
    ('akmenes-ams', 'Akmenės AMS'), ('alytaus-ams', 'Alytaus AMS'),
    ('anyksciu-ams', 'Anykščių AMS'), ('birstono-ams', 'Birštono AMS'),
    ('birzu-ams', 'Biržų AMS'), ('dotnuvos-ams', 'Dotnuvos AMS'),
    ('druskininku-ams', 'Druskininkų AMS'), ('duksto-ams', 'Dūkšto AMS'),
    ('elektrenu-ams', 'Elektrėnų AMS'), ('jonavos-ams', 'Jonavos AMS'),
    ('joniskio-ams', 'Joniškio AMS'), ('jurbarko-ams', 'Jurbarko AMS'),
    ('kaisiadoriu-ams', 'Kaišiadorių AMS'), ('kalvarijos-ams', 'Kalvarijos AMS'),
    ('kauno-ams', 'Kauno AMS'), ('kazlu-rudos-ams', 'Kazlų Rūdos AMS'),
    ('kelmes-ams', 'Kelmės AMS'), ('klaipedos-ams', 'Klaipėdos AMS'),
    ('kretingos-ams', 'Kretingos AMS'), ('kupiskio-ams', 'Kupiškio AMS'),
    ('kybartu-ams', 'Kybartų AMS'), ('laukuvos-ams', 'Laukuvos AMS'),
    ('lazdiju-ams', 'Lazdijų AMS'), ('marijampoles-ams', 'Marijampolės AMS'),
    ('mazeikiu-ams', 'Mažeikių AMS'), ('moletu-ams', 'Moletų AMS'),
    ('nidos-ams', 'Nidos AMS'), ('pagegiu-ams', 'Pagėgių AMS'),
    ('pakruojo-ams', 'Pakruojo AMS'), ('panevezio-ams', 'Panevėžio AMS'),
    ('plunges-ams', 'Plungės AMS'), ('prienu-ams', 'Prienų AMS'),
    ('raseiniu-ams', 'Raseinių AMS'), ('rietavo-ams', 'Rietavo AMS'),
    ('rokiskio-ams', 'Rokiškio AMS'), ('skuodo-ams', 'Skuodo AMS'),
    ('sakiu-ams', 'Šakių AMS'), ('salcininku-ams', 'Šalčininkų AMS'),
    ('seduvos-ams', 'Šeduvos AMS'), ('siauliu-ams', 'Šiaulių AMS'),
    ('silutes-ams', 'Šilutės AMS'), ('svencioniu-ams', 'Švenčionių AMS'),
    ('taurages-ams', 'Tauragės AMS'), ('telsiu-ams', 'Telšių AMS'),
    ('traku-ams', 'Trakų AMS'), ('ukmerges-ams', 'Ukmergės AMS'),
    ('utenos-ams', 'Utenos AMS'), ('varenos-ams', 'Varėnos AMS'),
    ('ventes-ams', 'Ventės AMS'), ('vezaiciu-ams', 'Vėžaičių AMS'),
    ('vilniaus-ams', 'Vilniaus AMS'), ('zarasu-ams', 'Zarasų AMS'),
]
STATION_BY_CODE = {code: name for code, name in stations}

START = "2016-04-24"
END = str(date.today())
OUTPUT_DIR = "meteo_data"
MAX_WORKERS = 4  # number of parallel threads for fetching data

def iter_days(start, end):
    current = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    while current < end_date:
        yield str(current)
        current = current.fromordinal(current.toordinal() + 1)


def wait_for_rate_limit_slot():
    while True:
        with rate_lock:
            now = time.monotonic()
            while request_timestamps and now - request_timestamps[0] >= 60:
                request_timestamps.popleft()

            if len(request_timestamps) < REQUESTS_PER_MINUTE:
                request_timestamps.append(now)
                return

            sleep_for = max(0.05, 60 - (now - request_timestamps[0]))
        time.sleep(sleep_for)


def normalize_observations(rows):
    normalized = []
    for row in rows:
        item = dict(row)
        if "observationTimeUtc" in item and "obs_time_utc" not in item:
            item["obs_time_utc"] = item["observationTimeUtc"]
        normalized.append(item)
    return normalized


def fetch_day(station_code, day_str, retries=3):
    url = f"{BASE_URL}/stations/{station_code}/observations/{day_str}"
    for attempt in range(retries):
        try:
            wait_for_rate_limit_slot()
            r = requests.get(url, timeout=30)
            if r.status_code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()

            payload = r.json()
            rows = payload.get("observations", [])
            if isinstance(rows, list):
                return normalize_observations(rows)
            return []
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # increasing wait time between retries
            else:
                print(f"  FAILED {station_code} {day_str}: {e}")
                return []

def write_station_csv(station_code, station_name, all_rows):
    out_path = os.path.join(OUTPUT_DIR, f"{station_code}.csv")
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.sort_values("obs_time_utc", inplace=True)
        df.to_csv(out_path, index=False)
        return f"OK {station_name}: {len(df)} rows"
    else:
        return f"EMPTY {station_name}"

def parse_args():
    parser = argparse.ArgumentParser(description="Bulk download meteo.lt API station data")
    def str_to_bool(value):
        if isinstance(value, bool):
            return value
        normalized = value.strip().lower()
        if normalized == "y":
            return True
        if normalized == "n":
            return False
        raise argparse.ArgumentTypeError("Expected 'y' or 'n'")

    parser.add_argument("--start", default=START, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=END, help="End date (YYYY-MM-DD) (up to but not including)")
    parser.add_argument(
        "--stations",
        default="all",
        help=(
            "Stations to download: 'all' or comma-separated station codes "
            "(e.g. vilniaus-ams,kauno-ams)"
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help="Total number of parallel chunk requests",
    )
    parser.add_argument(
        "--overwrite",
        type=str_to_bool,
        default=False,
        help="Overwrite the existing station CSV files (y/n)",
    )
    parser.add_argument(
        "--list-stations",
        action="store_true",
        help="Print all the available station codes and exit",
    )
    return parser.parse_args()


def parse_station_selection(stations_arg):
    if stations_arg.strip().lower() == "all":
        return stations

    selected_codes = [s.strip().lower() for s in stations_arg.split(",") if s.strip()]
    if not selected_codes:
        raise ValueError("No stations were provided.")

    unknown = [code for code in selected_codes if code not in STATION_BY_CODE]
    if unknown:
        known = ", ".join(sorted(STATION_BY_CODE.keys()))
        raise ValueError(f"Unknown station code(s): {', '.join(unknown)}\nKnown codes: {known}")

    # preserve user order and remove duplicates
    seen = set()
    selected = []
    for code in selected_codes:
        if code not in seen:
            selected.append((code, STATION_BY_CODE[code]))
            seen.add(code)
    return selected


def validate_date_range(start_date, end_date):
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    if s >= e:
        raise ValueError("start-date must be earlier than end-date")


def main():
    start_time = time.perf_counter()
    
    args = parse_args()

    if args.list_stations:
        for code, name in stations:
            print(f"{code} - {name}")
        return

    validate_date_range(args.start, args.end)
    selected_stations = parse_station_selection(args.stations)

    if args.workers < 1:
        raise ValueError("workers must be >= 1")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(
        "-----------------------------------------\n"
        f"Downloading {len(selected_stations)} stations with {args.workers} workers..."
        "\n-----------------------------------------"
    )
    print(f"Date range: {args.start} -> {args.end}")
    print(
        f"Output dir: {OUTPUT_DIR}\n"
        f"Overwrite existing files: {args.overwrite}\n"
        f"Rate limit: {REQUESTS_PER_MINUTE} requests/min\n"
        "-----------------------------------------"
    )

    days = list(iter_days(args.start, args.end))
    rows_by_station = {}
    remaining_chunks = {}
    station_names = {}
    for code, name in selected_stations:
        out_path = os.path.join(OUTPUT_DIR, f"{code}.csv")
        if os.path.exists(out_path) and not args.overwrite:
            print(f"SKIP {name}")
            continue
        rows_by_station[code] = []
        remaining_chunks[code] = len(days)
        station_names[code] = name

    day_jobs = [(code, day_str) for code in rows_by_station for day_str in days]

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_day, code, day_str): code
            for code, day_str in day_jobs
        }
        for future in as_completed(futures):
            code = futures[future]
            rows = future.result()
            if rows is not None:
                rows_by_station[code].extend(rows)
            remaining_chunks[code] -= 1
            if remaining_chunks[code] == 0:
                print(write_station_csv(code, station_names[code], rows_by_station[code]))
                del rows_by_station[code]

    end_time = time.perf_counter()
    elapsed = end_time - start_time

    print(
        "-----------------------------------------\n"
        f"All done! Elapsed time: {elapsed:.2f} seconds"
    )


if __name__ == "__main__":
    main()