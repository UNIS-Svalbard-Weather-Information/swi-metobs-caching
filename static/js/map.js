let additionalLayers = {};
let map;
let colorBar;

// Define default extent (latitude, longitude, zoom level)
const defaultExtent = {
    lat: 78.3, 
    lon: 16, 
    zoom: 8 
};

function loadMap(layerConfigUrl, mobileStationConfigUrl, fixedStationConfigUrl, windImagesUrl) {
    fetch(layerConfigUrl)
        .then(response => response.json())
        .then(layerConfig => {
            map = L.map('map').setView([defaultExtent.lat, defaultExtent.lon], defaultExtent.zoom);
            const baseLayers = {};
            additionalLayers = {};
            const layerControl = L.control.layers(baseLayers, additionalLayers).addTo(map);
            const legendControl = L.control({ position: 'bottomright' });

            legendControl.onAdd = function () {
                this._div = L.DomUtil.create('div', 'info legend');
                this.update();
                return this._div;
            };
            legendControl.update = function (layer) {
                updateLegend(layer, this);
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

            loadStations(mobileStationConfigUrl, fixedStationConfigUrl, windImagesUrl);

            // Initialize Leaflet Draw
            initializeLeafletDraw();

            // Add event listener for GPX file upload
            document.getElementById('upload-gpx').addEventListener('change', function (event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        const gpxData = e.target.result;
                        const gpxLayer = new L.GPX(gpxData, {
                            async: true
                        }).on('loaded', function (e) {
                            const geojson = gpxLayer.toGeoJSON();
                            L.geoJSON(geojson, {
                                onEachFeature: function (feature, layer) {
                                    drawnItems.addLayer(layer);
                                }
                            });
                            map.fitBounds(e.target.getBounds());
                        }).addTo(map);
                    };
                    reader.readAsText(file);
                }
            });
        });
}

function initializeLeafletDraw() {
    // Feature Group to store editable layers
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Leaflet Draw control
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        },
        draw: {
            polyline: true,
            polygon: false,
            circle: false,
            rectangle: false,
            marker: true,
            circlemarker: false
        }
    });
    map.addControl(drawControl);

    // Event listener for when a new layer is created
    map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        drawnItems.addLayer(layer);
    });

    // Add download button event listener
    document.getElementById('download-gpx').addEventListener('click', function () {
        downloadGPX(drawnItems);
    });
}

function downloadGPX(layerGroup) {
    const geojson = layerGroup.toGeoJSON();
    const gpx = togpx(geojson);
    
    const blob = new Blob([gpx], { type: 'application/gpx+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'map-drawings.gpx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}