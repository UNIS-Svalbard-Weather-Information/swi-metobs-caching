from source.maps_processing.sea_ice_map_processing import SeaIceCache

max_try = 10
i=1

while i < max_try:
    print(f"Try {i}/{max_try}")
    try:
        sea_ice_handler = SeaIceCache()

        sea_ice_handler.create_ice_chart_geojson()
        i= max_try+1
    except:
        i = i+1