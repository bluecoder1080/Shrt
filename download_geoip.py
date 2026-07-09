import os
import urllib.request

# Try multiple mirrors in order — the first one that works wins
DATABASE_URLS = [
    "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb",
    "https://github.com/dnomd343/GeoLite2/raw/download/Country.mmdb",
    "https://git.io/GeoLite2-Country.mmdb",
]
DATABASE_URL = DATABASE_URLS[0]
TARGET_DIR = os.path.join("app", "resources")
TARGET_FILE = os.path.join(TARGET_DIR, "GeoLite2-Country.mmdb")


def main():
    print("Checking/Creating resources directory...")
    os.makedirs(TARGET_DIR, exist_ok=True)

    if os.path.exists(TARGET_FILE):
        print(f"GeoIP Database already exists at {TARGET_FILE}. Skipping download.")
        return

    for url in DATABASE_URLS:
        print(f"Trying: {url}")
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(TARGET_FILE, "wb") as out_file:
                    out_file.write(response.read())
            print(f"Successfully downloaded database to {TARGET_FILE}")
            return
        except Exception as e:
            print(f"  Failed: {e}")
    print("All mirrors failed. The Celery worker will use 'Unknown' for country codes.")
    print("You can manually place GeoLite2-Country.mmdb in app/resources/ at any time.")


if __name__ == "__main__":
    main()
