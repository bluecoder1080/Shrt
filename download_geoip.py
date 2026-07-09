import os
import urllib.request

DATABASE_URL = "https://github.com/P3TERX/GeoLite2-Database/raw/download/GeoLite2-Country.mmdb"
TARGET_DIR = os.path.join("app", "resources")
TARGET_FILE = os.path.join(TARGET_DIR, "GeoLite2-Country.mmdb")

def main():
    print("Checking/Creating resources directory...")
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    if os.path.exists(TARGET_FILE):
        print(f"GeoIP Database already exists at {TARGET_FILE}. Skipping download.")
        return

    print(f"Downloading GeoLite2 Country database from: {DATABASE_URL}")
    try:
        # Define user-agent header to avoid bot blockers
        req = urllib.request.Request(
            DATABASE_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as response:
            with open(TARGET_FILE, "wb") as out_file:
                out_file.write(response.read())
        print(f"Successfully downloaded database to {TARGET_FILE}")
    except Exception as e:
        print(f"Error downloading GeoIP database: {str(e)}")
        print("Note: The Celery worker will fallback gracefully to 'Unknown' country codes if this file is missing.")

if __name__ == "__main__":
    main()
