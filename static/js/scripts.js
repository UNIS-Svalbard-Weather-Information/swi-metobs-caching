function loadMap(layerConfigUrl, mobileStationConfigUrl, beaufortImagesUrl) {
    fetch(layerConfigUrl)
        .then(response => response.json())
        .then(layerConfig => {
            const map = L.map('map').setView([0, 0], 2);
            const baseLayers = {};
            const additionalLayers = {};
            const layerControl = L.control.layers(baseLayers, additionalLayers).addTo(map);
            const legendControl = L.control({ position: 'bottomright' });

            // Function to fetch and update legend
            function updateLegend(layer) {
                if (!layer) {
                    legendControl._div.innerHTML = '';
                    return;
                }

                let legendHtml = '<h4>Legend</h4>';

                if (layer.type === 'wms') {
                    const legendUrl = `${layer.url}?SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=${layer.layers}`;
                    legendHtml += `<img src="${legendUrl}" alt="Legend">`;
                } else if (layer.type === 'arcgis') {
                    fetch(`${layer.url}/legend?f=pjson`)
                        .then(response => response.json())
                        .then(data => {
                            data.layers.forEach(layer => {
                                legendHtml += `<strong>${layer.layerName}</strong><br>`;
                                layer.legend.forEach(item => {
                                    legendHtml += `<img src="data:image/png;base64,${item.imageData}" alt="${item.label}"> ${item.label}<br>`;
                                });
                            });
                            legendControl._div.innerHTML = legendHtml;
                        });
                    return;
                }

                legendControl._div.innerHTML = legendHtml;
            }

            legendControl.onAdd = function () {
                this._div = L.DomUtil.create('div', 'info legend');
                this.update();
                return this._div;
            };
            legendControl.update = function (layer) {
                updateLegend(layer);
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
                    legendControl.update(layer);
                });

                // Clear legend when layer is removed
                layerObj.on('remove', function () {
                    legendControl.update(null);
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
