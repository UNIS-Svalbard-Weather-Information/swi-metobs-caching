function loadMap(layerConfigUrl, mobileStationConfigUrl, beaufortImagesUrl) {
    fetch(layerConfigUrl)
        .then(response => response.json())
        .then(layerConfig => {
            const map = L.map('map').setView([0, 0], 2);
            const baseLayers = {};
            const additionalLayers = {};
            const layerControl = L.control.layers(baseLayers, additionalLayers).addTo(map);
            const legendControl = L.control({ position: 'bottomright' });

            // Function to update legend
            function updateLegend(layerName) {
                let legendHtml = '<h4>Legend</h4>';
                if (layerName === 'Topp States') {
                    legendHtml += '<i style="background: #ff0000"></i> State 1<br>';
                    legendHtml += '<i style="background: #00ff00"></i> State 2<br>';
                    legendHtml += '<i style="background: #0000ff"></i> State 3<br>';
                    // Add more legend items as needed
                }
                // Add conditions for other layers here
                legendControl._div.innerHTML = legendHtml;
            }

            legendControl.onAdd = function () {
                this._div = L.DomUtil.create('div', 'info legend');
                this.update();
                return this._div;
            };
            legendControl.update = function (layerName) {
                updateLegend(layerName);
            };
            legendControl.addTo(map);

            // Process base maps
            layerConfig.baseMaps.forEach(layer => {
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
                if (Object.keys(baseLayers).length === 1) {
                    // Add the first base map to the map by default
                    layerObj.addTo(map);
                }
                layerControl.addBaseLayer(layerObj, layer.name);
            });

            // Process additional layers
            layerConfig.additionalLayers.forEach(layer => {
                let layerObj;
                switch (layer.type) {
                    case 'tile':
                        layerObj = L.tileLayer(layer.url);
                        break;
                    case 'arcgis':
                        layerObj = L.esri.dynamicMapLayer({ url: layer.url });
                        break;
                    case 'wms':
                        layerObj = L.tileLayer.wms(layer.url, {
                            layers: layer.layers,
                            format: 'image/png',
                            transparent: true
                        });
                        break;
                }
                additionalLayers[layer.name] = layerObj;
                layerControl.addOverlay(layerObj, layer.name);

                // Update legend when layer is added
                layerObj.on('add', function () {
                    legendControl.update(layer.name);
                });
            });

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
