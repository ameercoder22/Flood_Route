import asyncio
import os
from dotenv import load_dotenv
import earthaccess
import pystac_client
from app.config import get_settings

load_dotenv('backend/.env')
os.environ["EARTHDATA_USERNAME"] = os.getenv("NASA_EARTHDATA_USERNAME", "")
os.environ["EARTHDATA_PASSWORD"] = os.getenv("NASA_EARTHDATA_PASSWORD", "")

async def debug_all_catalogs():
    print("--- Debugging All Catalogs ---")
    earthaccess.login(strategy="environment")

    # The issue might be that NSIDC_ECS doesn't hold the NRT flood product
    # Let's search all NASA STAC headers
    # Instead of picking one catalog, let's query the main CMR STAC root

    root_catalog = pystac_client.Client.open("https://cmr.earthdata.nasa.gov/stac/")
    print(f"Root Catalog: {root_catalog}")

    # Try searching for the collection by ID globally across all catalogs

    target_collections = [
        "VCDWD_L3_F1_NRT",
        "VCDWD_L3_F2_NRT",
        "VCDWD_L3_F3_NRT",
        "VCDWD_L3_NRT"
    ]

    for col in target_collections:
        print(f"\nSearching for {col} across all catalogs...")
        found = False
        for cat in root_catalog.get_children():
            try:
                # print(f"Checking catalog: {cat.id}")
                search = cat.search(collections=[col], max_items=1)
                items = search.item_collection()
                if len(items) > 0:
                    print(f"FOUND IN: {cat.id}")
                    found = True
            except:
                continue
        if not found:
            print("Not found in child catalogs.")

    # Also check if it exists if we just search by ID using CMR API (not STAC)
    print("\n--- Trying CMR API Search (non-STAC) ---")
    import requests
    for col in target_collections:
        url = f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name={col}&page_size=1"
        resp = requests.get(url)
        print(f"{col}: {len(resp.json()['feed']['entry'])} granules found")

if __name__ == "__main__":
    asyncio.run(debug_all_catalogs())
