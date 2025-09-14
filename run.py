from source.cacheHandler.cacheHandler import CacheHandler

import os

if not os.path.exists('/.dockerenv'):
    import dotenv

    dotenv.load_dotenv(".env")

station_handler = CacheHandler()

station_handler.cache_stations_status()
station_handler.cache_realtime_data()
station_handler.cache_past_hourly_data()