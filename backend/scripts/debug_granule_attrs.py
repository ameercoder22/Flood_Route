import asyncio
import os
from dotenv import load_dotenv
import earthaccess
from app.config import get_settings

load_dotenv('backend/.env')
os.environ["EARTHDATA_USERNAME"] = os.getenv("NASA_EARTHDATA_USERNAME", "")
os.environ["EARTHDATA_PASSWORD"] = os.getenv("NASA_EARTHDATA_PASSWORD", "")

async def debug_granule_attributes():
    print("--- Debug Granule Attributes ---")
    earthaccess.login(strategy="environment")
    bbox = (88.0, 24.0, 90.0, 26.0)
    results = earthaccess.search_data(
        short_name="VCDWD_L3_NRT",
        bounding_box=bbox,
        temporal=("2026-09-01", "2026-09-20"),
        count=1
    )
    if results:
        granule = results[0]
        print(f"Granule type: {type(granule)}")
        print(f"Granule keys: {granule.keys()}")
        print(f"Granule attributes: {dir(granule)}")
    else:
        print("No granules found")

if __name__ == "__main__":
    asyncio.run(debug_granule_attributes())
