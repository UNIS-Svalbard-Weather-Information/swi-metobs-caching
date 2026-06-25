from source.cacheHandler.cacheHandler import CacheHandler


def main():
    station_handler = CacheHandler()

    station_handler.cache_stations_status()
    station_handler.cache_realtime_data()
    station_handler.cache_past_hourly_data()


if __name__ == "__main__":
    main()
