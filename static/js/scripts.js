let additionalLayers = {};
let map;

function loadMap(layerConfigUrl, mobileStationConfigUrl, windImagesUrl) {
    fetch(layerConfigUrl)
        .then(response => response.json())
        .then(layerConfig => {
            map = L.map('map').setView([0, 0], 2);
            const baseLayers = {};
            additionalLayers = {};
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

                // Update legend and add opacity control when layer is added
                layerObj.on('add', function () {
                    legendControl.update(layer);
                    addOpacityControl(layer.name, layerObj);
                });

                // Clear legend and remove opacity control when layer is removed
                layerObj.on('remove', function () {
                    legendControl.update(null);
                    removeOpacityControl(layer.name);
                });
            });

            fetch(mobileStationConfigUrl)
                .then(response => response.json())
                .then(mobileStations => {
                    const durationSelect = document.getElementById('track-duration-select');
                    durationSelect.addEventListener('change', () => {
                        const duration = parseInt(durationSelect.value, 10);
                        mobileStations.forEach(station => {
                            fetchMobileStationData(station, map, windImagesUrl, duration);
                        });
                    });

                    // Initial load with default duration (1 hour)
                    const initialDuration = parseInt(durationSelect.value, 10);
                    mobileStations.forEach(station => {
                        fetchMobileStationData(station, map, windImagesUrl, initialDuration);
                    });
                });
        });
}

function fetchMobileStationData(station, map, windImagesUrl, duration) {
    fetch(`/api/mobile-station-data/${station.id}?duration=${duration}`)
        .then(response => response.json())
        .then(data => {
            const iconUrl = getWindSpeedIcon(windImagesUrl, data.windSpeed);
            const icon = L.icon({
                iconUrl: iconUrl,
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });

            const mobileMarker = L.marker([data.lat, data.lon], { icon: icon }).addTo(map);
            mobileMarker.bindPopup(`Boat: ${station.name}<br>Wind Speed: ${data.windSpeed} kts<br>Wind Direction: ${data.windDirection}°`);

            const polyline = L.polyline(data.track, { color: 'blue' }).addTo(map);
        });
}

function getWindSpeedIcon(basePath, windSpeed) {
    const windSpeeds = [0, 5, 10, 15, 20, 25, 30, 35, 50, 55, 60, 65, 100, 105];
    let closest = windSpeeds.reduce((prev, curr) => Math.abs(curr - windSpeed) < Math.abs(prev - windSpeed) ? curr : prev);
    return `${basePath}/${closest.toString().padStart(2, '0')}kts.gif`;
}

function addOpacityControl(layerName, layerObj) {
    const opacityControls = document.getElementById('opacity-controls');
    const controlHtml = `
        <div class="opacity-control" id="opacity-${layerName}">
            <label>${layerName}</label>
            <input type="range" min="0" max="100" value="100" onchange="updateLayerOpacity('${layerName}', this.value)">
        </div>
    `;
    opacityControls.insertAdjacentHTML('beforeend', controlHtml);
}

function removeOpacityControl(layerName) {
    const control = document.getElementById(`opacity-${layerName}`);
    if (control) {
        control.remove();
    }
}

function updateLayerOpacity(layerName, value) {
    const layer = additionalLayers[layerName];
    if (layer) {
        layer.setOpacity(value / 100);
    }
}
