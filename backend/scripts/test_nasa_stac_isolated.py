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

async def isolated_nasa_test():
    print("--- Isolated NASA STAC Query Test (Broader Search) ---")

    # Authenticate
    try:
        earthaccess.login(strategy="environment")
        print("NASA AUTHENTICATION: PASS")
    except Exception as e:
        print(f"NASA AUTHENTICATION: FAIL ({e})")
        return

    # Query STAC
    try:
        catalog = pystac_client.Client.open("https://cmr.earthdata.nasa.gov/stac/NSIDC_ECS")
        # Broader scope to find ANY available flood data
        bbox = (-180, -90, 180, 90)

        search = catalog.search(
            collections=["VIIRS_NRT_FLOOD_L3"],
            bbox=bbox,
            datetime="2026-09-01/2026-09-20",
            max_items=3
        )
        items = search.item_collection()
        print("NASA STAC QUERY: PASS")
        print(f"NASA STAC ITEMS FOUND: {len(items)}")

        if len(items) > 0:
            print("REAL NASA FLOOD PRODUCT FOUND: YES")
            for item in items:
                print(f"\nItem ID: {item.id}")
                print(f"Collection: {item.collection_id}")
                print(f"Datetime: {item.datetime}")
                print(f"BBox: {item.bbox}")
                print(f"Assets: {list(item.assets.keys())}")
        else:
            print("REAL NASA FLOOD PRODUCT FOUND: NO")

    except Exception as e:
        print(f"NASA STAC QUERY: FAIL ({e})")

if __name__ == "__main__":
    asyncio.run(isolated_nasa_test())
