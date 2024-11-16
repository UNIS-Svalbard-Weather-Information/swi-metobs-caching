let additionalLayers = {};
let map;
let drawnItems;
let colorBar;
let activeLayers = {};

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
            //const additionalLayers = {};
            const layerControl = L.control.layers(baseLayers, additionalLayers).addTo(map);
            const legendControl = L.control({ position: 'bottomright' });

            legendControl.onAdd = function () {
                this._div = L.DomUtil.create('div', 'info legend');
                this.update();
                return this._div;
            };
            legendControl.update = function () {
                updateLegend(this);
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
                        layerObj = L.esri.dynamicMapLayer({
                            url: layer.url,
                            layers: layer.layers
                        });
                        break;
                    case 'wms':
                        layerObj = L.tileLayer.wms(layer.url, {
                            layers: layer.layers,
                            format: 'image/png',
                            transparent: true
                        });
                        break;
                     case 'geojson':
                        fetch(layer.url)
                            .then(response => response.json())
                            .then(geojsonData => {
                                // Define a style function based on feature properties
                                const style = feature => ({
                                    color: feature.properties.color || 'black', // Contour color
                                    weight: feature.properties.weight || 2,    // Contour weight
                                    opacity: feature.properties.opacity || 1,  // Contour opacity
                                    fillColor: feature.properties.color || 'blue', // Fill color
                                    fillOpacity: feature.properties.fillOpacity || 0.9 // Fill opacity
                                });

                                // Create the GeoJSON layer with the style function
                                const geojsonLayer = L.geoJSON(geojsonData, { style });

                                additionalLayers[layer.name] = geojsonLayer;
                                layerControl.addOverlay(geojsonLayer, layer.name);

                                // Update active layers and legend when a layer is added
                                geojsonLayer.on('add', function () {
                                    activeLayers[layer.name] = layer;
                                    legendControl.update();
                                    addOpacityControl(layer.name, geojsonLayer);
                                });

                                // Remove from active layers and update legend when a layer is removed
                                geojsonLayer.on('remove', function () {
                                    delete activeLayers[layer.name];
                                    legendControl.update();
                                    removeOpacityControl(layer.name);
                                });
                            });
                        return;
                }
                additionalLayers[layer.name] = layerObj;
                layerControl.addOverlay(layerObj, layer.name);

                // Update active layers and legend when a layer is added
                layerObj.on('add', function () {
                    activeLayers[layer.name] = layer;
                    legendControl.update();
                    addOpacityControl(layer.name, layerObj);
                });

                // Remove from active layers and update legend when a layer is removed
                layerObj.on('remove', function () {
                    delete activeLayers[layer.name];
                    legendControl.update();
                    removeOpacityControl(layer.name);
                });
            });

            loadStations(mobileStationConfigUrl, fixedStationConfigUrl, windImagesUrl);

            // Initialize Leaflet Draw
            initializeLeafletDraw();

            // Initialize Leaflet Measure
            initializeLeafletMeasure();

            // Add event listener for GPX file upload
            document.getElementById('upload-gpx').addEventListener('change', handleGPXUpload);
        });
}


function initializeLeafletMeasure() {
    // Initialize Leaflet Measure
    const measureControl = new L.Control.Measure({
        position: 'topleft',
        primaryLengthUnit: 'meters',
        secondaryLengthUnit: 'kilometers',
        primaryAreaUnit: 'sqmeters',
        secondaryAreaUnit: 'sqkilometers',
    });
    map.addControl(measureControl);
}

function initializeLeafletDraw() {
    // Feature Group to store editable layers
    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Leaflet Draw control with custom feature colors
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        },
        draw: {
            polyline: {
                shapeOptions: {
                    color: '#FF0000', // Red color
                    weight: 4
                }
            },
            polygon: {
                shapeOptions: {
                    color: '#FF0000' // Red color
                }
            },
            circle: {
                shapeOptions: {
                    color: '#FF0000' // Red color
                }
            },
            rectangle: {
                shapeOptions: {
                    color: '#FF0000' // Red color
                }
            },
            marker: {
                icon: L.icon({
                    iconUrl: 'static/images/map_drawing_element/pin.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                })
            },
            circlemarker: {
                color: '#FF0000' // Red color
            }
        }
    });
    map.addControl(drawControl);

    // Event listener for when a new layer is created
    map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        drawnItems.addLayer(layer);

        // Display coordinates if the layer is a marker
        if (layer instanceof L.Marker) {
            displayMarkerCoordinates(layer);
        }

        // Display length if the layer is a polyline
        if (layer instanceof L.Polyline) {
            displayPolylineLength(layer);
        }
    });

    // Event listener for when an existing layer is edited
    map.on('draw:edited', function (event) {
        const layers = event.layers;
        layers.eachLayer(function (layer) {
            if (layer instanceof L.Polyline) {
                displayPolylineLength(layer);
            }
        });
    });

    // Add download button event listener
    document.getElementById('download-gpx').addEventListener('click', function () {
        downloadGPX(drawnItems);
    });
}

function displayMarkerCoordinates(marker) {
    const latlng = marker.getLatLng();
    const popupContent = `Coordinates: ${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;
    const popup = L.popup()
        .setLatLng(latlng)
        .setContent(popupContent)
        .openOn(map);

    // Bind the popup to the marker
    marker.bindPopup(popup);
}

function displayPolylineLength(polyline) {
    const latlngs = polyline.getLatLngs();
    const length = calculateLength(latlngs);
    const lengthInKm = (length / 1000).toFixed(2); // Convert meters to kilometers and round to 2 decimal places

    // Create a popup with the length information
    const popupContent = `Length: ${lengthInKm} km`;
    const popup = L.popup()
        .setLatLng(polyline.getBounds().getCenter())
        .setContent(popupContent)
        .openOn(map);

    // Bind the popup to the polyline
    polyline.bindPopup(popup);
}

function calculateLength(latlngs) {
    let length = 0;
    for (let i = 0; i < latlngs.length - 1; i++) {
        length += latlngs[i].distanceTo(latlngs[i + 1]);
    }
    return length;
}

function handleGPXUpload(event) {
    const files = event.target.files;
    Array.from(files).forEach(file => {
        const reader = new FileReader();
        reader.onload = function (e) {
            const gpxData = e.target.result;
            const gpxLayer = new L.GPX(gpxData, {
                async: true
            }).on('loaded', function (e) {
                const geojson = gpxLayer.toGeoJSON();
                const filteredGeojson = filterGeoJSON(geojson);
                
                // Clear existing layers
                //drawnItems.clearLayers();
                
                // Add the filtered GeoJSON data to the drawnItems layer group
                L.geoJSON(filteredGeojson, {
                    onEachFeature: function (feature, layer) {
                        drawnItems.addLayer(layer);

                        // Calculate and display length if the feature is a polyline
                        if (feature.geometry.type === 'LineString') {
                            displayPolylineLength(layer);
                        }
                    }
                });
                
                // Adjust the map view to fit the bounds of the new data
                const bounds = L.geoJSON(filteredGeojson).getBounds();
                map.fitBounds(bounds);
            });
        };
        reader.readAsText(file);
    });
}

function filterGeoJSON(geojson) {
    // Filter the GeoJSON to include only polylines and points
    return {
        type: 'FeatureCollection',
        features: geojson.features.filter(feature => 
            feature.geometry.type === 'LineString' || feature.geometry.type === 'Point'
        )
    };
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
