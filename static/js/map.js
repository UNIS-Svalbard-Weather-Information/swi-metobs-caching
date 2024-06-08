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
        });
}
