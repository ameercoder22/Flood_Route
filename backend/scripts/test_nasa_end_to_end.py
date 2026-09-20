import asyncio
import os
from dotenv import load_dotenv

# 1. Load environment and set required variables FIRST
load_dotenv('backend/.env')
os.environ["EARTHDATA_USERNAME"] = os.getenv("NASA_EARTHDATA_USERNAME", "")
os.environ["EARTHDATA_PASSWORD"] = os.getenv("NASA_EARTHDATA_PASSWORD", "")

# 2. Imports AFTER env setup
from app.services.nasa_flood_service import NASAFloodService
from app.services.exposure_service import calculate_flood_exposure

async def verify_flood_integration():
    service = NASAFloodService()

    # Test region: Bangladesh/India border area, known for high flood activity.
    # Timeframe: Recent.
    bbox = (88.0, 24.0, 90.0, 26.0)

    print(f"--- Testing Pipeline for BBox: {bbox} ---")

    try:
        # 1. Retrieve data
        flood_data = await service.get_flood_extent(bbox)

        features = flood_data.get("features", [])
        if not features:
            print("ACTUAL FLOOD OBSERVATION RETRIEVED: NO")
            print("Result: No flood observations found for requested region/timeframe.")
            return

        print("ACTUAL FLOOD OBSERVATION RETRIEVED: YES")

        # Product Metadata
        props = features[0].get("properties", {})
        print(f"NASA Product: {props.get('source')}")
        print(f"Granule ID: {props.get('granule_id')}")
        print(f"Observation Time: {props.get('observation_time')}")
        print(f"Features Retrieved: {len(features)}")

        # 2. Test Analysis
        route = [
            {"latitude": 25.0, "longitude": 89.0},
            {"latitude": 25.1, "longitude": 89.1}
        ]

        analysis = calculate_flood_exposure(route, flood_data)

        print("\n--- Route Spatial Analysis ---")
        print(f"Result: {analysis}")

    except Exception as e:
        print(f"PIPELINE FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(verify_flood_integration())
