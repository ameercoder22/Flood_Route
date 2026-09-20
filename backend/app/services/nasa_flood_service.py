import logging
import os
import earthaccess
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class NASAFloodService:
    """
    Service to retrieve near-real-time NASA flood observations (VIIRS-based).
    Uses NASA Earthdata/CMR API for querying granules.
    """

    def __init__(self):
        # Earthdata Login credentials
        self.username = settings.nasa_earthdata_username
        self.password = settings.nasa_earthdata_password
        self.is_authenticated = False

    def _login(self):
        if self.is_authenticated:
            return

        # Earthaccess reads from EARTHDATA_USERNAME/PASSWORD env vars
        os.environ["EARTHDATA_USERNAME"] = self.username
        os.environ["EARTHDATA_PASSWORD"] = self.password

        try:
            earthaccess.login(strategy="environment")
            self.is_authenticated = True
            logger.info("Successfully authenticated with NASA Earthdata.")
        except Exception as e:
            logger.error("Failed to authenticate with NASA Earthdata: %s", e)
            raise

    async def get_flood_extent(self, bbox: tuple[float, float, float, float]) -> dict:
        if settings.demo_mode:
            logger.info("DEMO_MODE active: returning simulated NASA flood data.")
            return self._get_simulated_flood_extent(bbox)

        self._login()

        logger.info("Fetching REAL NASA flood granules for bbox: %s", bbox)

        try:
            # Search CMR for the VIIRS NRT collection
            # Use 'VCDWD_L3_NRT' as the umbrella collection
            results = earthaccess.search_data(
                short_name="VCDWD_L3_NRT",
                bounding_box=bbox,
                temporal=("2026-09-01", "2026-09-20"),
                count=1
            )

            if not results:
                logger.warning("No NASA flood granules found.")
                return {"type": "FeatureCollection", "features": []}

            granule = results[0]
            logger.info("Found NASA Granule: %s", granule.uuid)

            # Return metadata
            return {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "source": "NASA VIIRS Global Flood Product (REAL NRT)",
                        "observation_time": granule['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime'],
                        "granule_id": granule.uuid,
                        "data_url": granule.data_links()[0] if granule.data_links() else None
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [bbox[0], bbox[1]],
                            [bbox[2], bbox[1]],
                            [bbox[2], bbox[3]],
                            [bbox[0], bbox[3]],
                            [bbox[0], bbox[1]]
                        ]]
                    }
                }]
            }

        except Exception as e:
            logger.error("Error retrieving NASA data: %s", e)
            raise

    def _get_simulated_flood_extent(self, bbox: tuple[float, float, float, float]) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "source": "DEMO DATA — NOT NASA OBSERVATION",
                    "observation_time": "2026-09-20T00:00:00Z"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [bbox[0], bbox[1]],
                        [bbox[2], bbox[1]],
                        [bbox[2], bbox[3]],
                        [bbox[0], bbox[3]],
                        [bbox[0], bbox[1]]
                    ]]
                }
            }]
        }
