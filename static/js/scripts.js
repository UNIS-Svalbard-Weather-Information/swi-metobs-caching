function loadMap(layerConfigUrl, mobileStationConfigUrl, beaufortImagesUrl) {
    fetch(layerConfigUrl)
        .then(response => response.json())
        .then(layerConfig => {
            const map = L.map('map').setView([0, 0], 2);
            const layerControl = L.control.layers().addTo(map);
            const baseLayers = {};

            layerConfig.forEach(layer => {
                let layerObj;
                switch (layer.type) {
                    case 'tile':
                        layerObj = L.tileLayer(layer.url);
                        break;
                    case 'arcgis':
                        layerObj = L.esri.tiledMapLayer({ url: layer.url });
                        break;
                    case 'wms':
                        layerObj = L.tileLayer.wms(layer.url, {
                            layers: layer.layers,
                            format: 'image/png',
                            transparent: true
                        });
                        break;
                }
                baseLayers[layer.name] = layerObj;
                layerControl.addBaseLayer(layerObj, layer.name);
            });

            baseLayers[Object.keys(baseLayers)[0]].addTo(map);

            fetch(mobileStationConfigUrl)
                .then(response => response.json())
                .then(mobileStations => {
                    mobileStations.forEach(station => {
                        fetchMobileStationData(station, map, beaufortImagesUrl);
                    });
                });
        });
}

function fetchMobileStationData(station, map, beaufortImagesUrl) {
    fetch(`/api/mobile-station-data/${station.id}`)
        .then(response => response.json())
        .then(data => {
            const iconUrl = `${beaufortImagesUrl}/${data.windBeaufort}.png`;
            const icon = L.icon({
                iconUrl: iconUrl,
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });

            const mobileMarker = L.marker([data.lat, data.lon], { icon: icon }).addTo(map);
            mobileMarker.bindPopup(`Boat: ${station.name}<br>Wind Speed: ${data.windSpeed} m/s<br>Wind Direction: ${data.windDirection}°`);

            const polyline = L.polyline(data.track, { color: 'blue' }).addTo(map);
        });
}
