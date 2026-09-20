import asyncio
import os
from dotenv import load_dotenv
import earthaccess
import pystac_client
from app.config import get_settings

# Load environment variables
load_dotenv('backend/.env')

# Map to earthaccess expected env vars
os.environ["EARTHDATA_USERNAME"] = os.getenv("NASA_EARTHDATA_USERNAME", "")
os.environ["EARTHDATA_PASSWORD"] = os.getenv("NASA_EARTHDATA_PASSWORD", "")

async def debug_nasa_collections():
    print("--- Debugging NASA Collections ---")

    # 1. Authenticate
    try:
        earthaccess.login(strategy="environment")
        print("NASA AUTHENTICATION: PASS")
    except Exception as e:
        print(f"NASA AUTHENTICATION: FAIL ({e})")
        return

    # 2. Query Setup
    # Current suspect: collection ID might be wrong (e.g. looking for VIIRS_NRT_FLOOD_L3 instead of VCDWD_L3_NRT)
    collections_to_test = [
        "VCDWD_L3_F1_NRT",
        "VCDWD_L3_F2_NRT",
        "VCDWD_L3_F3_NRT",
        "VCDWD_L3_NRT"
    ]

    # Use a broad timeframe known for data
    # (Checking data from early Sep 2026 as per date context)
    timeframe = "2026-09-01/2026-09-20"

    # Use global bbox for initial catalog verification
    bbox = (-180, -90, 180, 90)

    results_table = []

    try:
        catalog = pystac_client.Client.open("https://cmr.earthdata.nasa.gov/stac/NSIDC_ECS")
        print(f"Connected to CMR STAC: {catalog}")
    except Exception as e:
        print(f"Failed to connect to STAC: {e}")
        return

    for col in collections_to_test:
        try:
            print(f"\nTesting collection: {col}")
            search = catalog.search(
                collections=[col],
                bbox=bbox,
                datetime=timeframe,
                max_items=1
            )
            items = search.item_collection()
            count = len(items)
            results_table.append((col, timeframe, "Global", count, "PASS"))
            print(f"Items returned: {count}")
            if count > 0:
                print(f"Sample Item: {items[0].id}")
                print(f"Sample Assets: {list(items[0].assets.keys())}")
        except Exception as e:
            results_table.append((col, timeframe, "Global", 0, f"FAIL: {str(e)[:20]}"))
            print(f"Query FAIL: {e}")

    print("\n--- Summary Table ---")
    print(f"{'Collection':<20} | {'Date range':<20} | {'BBox':<10} | {'Items':<6} | {'Result'}")
    print("-" * 80)
    for row in results_table:
        print(f"{row[0]:<20} | {row[1]:<20} | {row[2]:<10} | {row[3]:<6} | {row[4]}")

if __name__ == "__main__":
    asyncio.run(debug_nasa_collections())
