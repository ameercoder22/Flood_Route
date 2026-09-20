import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# Map to earthaccess expected env vars
os.environ["EARTHDATA_USERNAME"] = os.getenv("NASA_EARTHDATA_USERNAME", "")
os.environ["EARTHDATA_PASSWORD"] = os.getenv("NASA_EARTHDATA_PASSWORD", "")

from app.services.nasa_flood_service import NASAFloodService

async def test_real_nasa_data():
    service = NASAFloodService()
    # The service will use the env vars now

    # Test bounding box (Kurnool area example)
    bbox = (78.0, 15.8, 78.1, 15.9)

    try:
        print("Testing real NASA flood data retrieval...")
        data = await service.get_flood_extent(bbox)
        print("Data retrieved successfully!")

        # Verify it's not simulated
        features = data.get("features", [])
        if features:
            props = features[0].get("properties", {})
            source = props.get("source", "")
            print(f"Source: {source}")
            if "DEMO DATA" in source:
                print("FAILED: Retrieved Demo Data instead of Real NASA Data.")
            else:
                print("SUCCESS: Retrieved Real NASA Data.")
                print(f"Observation Time: {props.get('observation_time')}")
        else:
            print("No features found for this area.")

    except Exception as e:
        print(f"FAILED: Error retrieving NASA data: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_nasa_data())
