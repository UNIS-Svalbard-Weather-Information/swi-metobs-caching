let additionalLayers = {};
let map;
let drawnItems;
let colorBar;
let activeLayers = {};

let configVariablesLoaded = false;
let configVariablesData = null;

// Define default extent (latitude, longitude, zoom level)
const defaultExtent = {
    lat: 78.3, 
    lon: 16, 
    zoom: 8 
};

/**
 * Initializes a dynamic, interactive map with configurable base layers, additional layers, controls, and functionalities.
 *
 * This function fetches configuration data for base maps and additional layers, sets up the Leaflet map,
 * and integrates features such as legends, controls, layer toggling, opacity adjustments,
 * station overlays, and user-drawn geometries. It also enables GPX file uploads for
 * adding external data to the map.
 *
 * @param {string} layerConfigUrl - URL to the JSON configuration file containing base maps and additional layers.
 * @param {string} mobileStationConfigUrl - URL to the configuration data for mobile stations to be displayed on the map.
 * @param {string} fixedStationConfigUrl - URL to the configuration data for fixed stations to be displayed on the map.
 * @param {string} windImagesUrl - (Optional) URL to wind image overlays for visualization.
 *
 * Features:
 * - **Base Layers**: Supports Tile, ArcGIS, and WMS layers. Automatically displays the first base map as default.
 * - **Additional Layers**: Includes Tile, ArcGIS, WMS, and GeoJSON layers with styling and interactivity.
 * - **Legend and Controls**: Dynamically updates a legend based on active layers and provides controls for toggling layers.
 * - **Opacity Control**: Allows users to adjust the transparency of additional layers.
 * - **GPX Uploads**: Enables uploading and displaying GPX files with filtering and feature integration.
 * - **Custom Draw Features**: Integrates Leaflet Draw for drawing and editing geometries on the map.
 * - **Measurement Tools**: Adds tools for measuring distances and areas directly on the map.
 * - **Responsive View**: Automatically adjusts the map view to fit the bounds of uploaded or dynamically added data.
 *
 * Dependencies:
 * - Requires Leaflet and associated plugins, including:
 *   - `L.Control.Layers` for layer management.
 *   - `L.Control.Draw` for drawing and editing geometries.
 *   - `L.Control.Measure` for measurement tools.
 *   - `togpx` library for exporting data in GPX format.
 *   - Leaflet GPX plugin for parsing GPX files.
 *
 * Example Usage:
 * ```javascript
 * loadMap(
 *   '/config/layerConfig.json',
 *   '/config/mobileStations.json',
 *   '/config/fixedStations.json',
 *   '/overlays/windImages'
 * );
 * ```
 */
function loadMap(layerConfigUrl, mobileStationConfigUrl, fixedStationConfigUrl, windImagesUrl) {
    // Call loadStations without waiting for it to complete
    loadStations(windImagesUrl);

    fetch(layerConfigUrl)
        .then(response => response.json())
        .then(layerConfig => {
            map = L.map('map').setView([defaultExtent.lat, defaultExtent.lon], defaultExtent.zoom);

            const baseLayersTree = {
                label: 'Base Layers',
                children: []
            };
            additionalLayers = {};

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

                addLayerToTree(baseLayersTree, layer.category, layer.name, layerObj);

                if (layer.default || Object.keys(baseLayersTree.children).length === 1) {
                    layerObj.addTo(map);
                }
            });

            const overlayLayersTree = {
                label: 'Overlay Layers',
                children: []
            };

            const geoJsonLayers = [];

            const geoJsonPromises = layerConfig.additionalLayers.map(layer => {
                if (layer.type === 'geojson') {
                    return fetch(layer.url)
                        .then(response => response.json())
                        .then(geojsonData => {
                            const style = feature => ({
                                color: feature.properties.color || 'black',
                                weight: feature.properties.weight || 2,
                                opacity: feature.properties.opacity || 1,
                                fillColor: feature.properties.color || 'blue',
                                fillOpacity: feature.properties.fillOpacity || 0.9
                            });

                            const geojsonLayer = L.geoJSON(geojsonData, { style });
                            additionalLayers[layer.name] = geojsonLayer;
                            addLayerToTree(overlayLayersTree, layer.category, layer.name, geojsonLayer);

                            if (layer.default) {
                                geojsonLayer.addTo(map);
                                activeLayers[layer.name] = layer;
                                legendControl.update();
                            }

                            geojsonLayer.on('add', function () {
                                activeLayers[layer.name] = layer;
                                legendControl.update();
                                addOpacityControl(layer.name, geojsonLayer);
                            });
                            geojsonLayer.on('remove', function () {
                                delete activeLayers[layer.name];
                                legendControl.update();
                                removeOpacityControl(layer.name);
                            });

                            geoJsonLayers.push({ layer, geojsonLayer });
                        });
                } else {
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
                    }

                    additionalLayers[layer.name] = layerObj;
                    addLayerToTree(overlayLayersTree, layer.category, layer.name, layerObj);

                    if (layer.default) {
                        layerObj.addTo(map);
                        activeLayers[layer.name] = layer;
                        legendControl.update();
                    }

                    layerObj.on('add', function () {
                        activeLayers[layer.name] = layer;
                        legendControl.update();
                        addOpacityControl(layer.name, layerObj);
                    });
                    layerObj.on('remove', function () {
                        delete activeLayers[layer.name];
                        legendControl.update();
                        removeOpacityControl(layer.name);
                    });
                }
            });

            Promise.all(geoJsonPromises).then(() => {
                L.control.layers.tree(baseLayersTree, overlayLayersTree, {
                    collapsed: true
                }).addTo(map);

                initializeLeafletDraw();
                initializeLeafletMeasure();
                document.getElementById('upload-gpx').addEventListener('change', handleGPXUpload);

                // Set up interval to refetch GeoJSON data every 15 minutes
                setInterval(() => {
                    geoJsonLayers.forEach(({ layer, geojsonLayer }) => {
                        fetch(layer.url)
                            .then(response => response.json())
                            .then(geojsonData => {
                                geojsonLayer.clearLayers().addData(geojsonData);
                                legendControl.update(); // Update legend after refetching data
                            });
                    });
                }, 900000); // 900000 milliseconds = 15 minutes
            });
        });
}


// Helper function to add layers to the tree structure
function addLayerToTree(tree, category, name, layer) {
    let categoryNode = tree.children.find(child => child.label === category);
    if (!categoryNode) {
        categoryNode = { label: category, children: [] };
        tree.children.push(categoryNode);
    }
    categoryNode.children.push({ label: name, layer });
}

/**
 * Initializes the Leaflet Measure tool on the map.
 *
 * This tool allows users to measure distances and areas directly on the map.
 * It adds a control to the top-left corner of the map interface, providing an interactive way to
 * calculate lengths (e.g., meters, kilometers) and areas (e.g., square meters, square kilometers).
 *
 * Features:
 * - Primary unit for length: meters.
 * - Secondary unit for length: kilometers.
 * - Primary unit for area: square meters.
 * - Secondary unit for area: square kilometers.
 *
 * Dependencies:
 * - Requires the Leaflet.Measure plugin to be included in the project.
 */
function initializeLeafletMeasure() {
    // Create a measure control with specified options
    const measureControl = new L.Control.Measure({
        position: 'topleft',            // Position of the control on the map
        primaryLengthUnit: 'meters',    // Primary unit for length measurement
        secondaryLengthUnit: 'kilometers', // Secondary unit for length measurement
        primaryAreaUnit: 'sqmeters',    // Primary unit for area measurement
        secondaryAreaUnit: 'sqkilometers' // Secondary unit for area measurement
    });

    // Add the measure control to the map
    map.addControl(measureControl);
}


/**
 * Initializes the Leaflet Draw tool on the map.
 *
 * This tool allows users to draw, edit, and manage various geometries (e.g., polylines, polygons, circles)
 * on the map. The function adds a drawing control panel and sets up event listeners to handle
 * user interactions, such as creating new features, editing existing ones, and downloading them in GPX format.
 *
 * Features:
 * - Supports drawing polylines, polygons, rectangles, circles, and markers.
 * - Customizable feature styles (e.g., red color, marker icons).
 * - Allows editing of previously drawn geometries.
 * - Displays additional information, such as coordinates for markers and lengths for polylines.
 * - Enables downloading drawn features as GPX files.
 *
 * Dependencies:
 * - Requires the Leaflet.Draw plugin to be included in the project.
 */
function initializeLeafletDraw() {
    // Create a FeatureGroup to store user-drawn layers
    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Initialize the Leaflet Draw control with custom options
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems // Allow editing layers in the drawnItems group
        },
        draw: {
            polyline: { // Options for polylines
                shapeOptions: {
                    color: '#FF0000', // Red color for polylines
                    weight: 4         // Thickness of polylines
                }
            },
            polygon: { // Options for polygons
                shapeOptions: {
                    color: '#FF0000' // Red color for polygon edges
                }
            },
            circle: { // Options for circles
                shapeOptions: {
                    color: '#FF0000' // Red color for circle outlines
                }
            },
            rectangle: { // Options for rectangles
                shapeOptions: {
                    color: '#FF0000' // Red color for rectangle outlines
                }
            },
            marker: { // Options for markers
                icon: L.icon({
                    iconUrl: 'static/images/map_drawing_element/pin.png', // Custom pin icon
                    iconSize: [25, 41],   // Size of the marker icon
                    iconAnchor: [12, 41], // Anchor point for the marker
                    popupAnchor: [1, -34], // Position of the popup relative to the marker
                    shadowSize: [41, 41]  // Shadow size for the marker
                })
            },
            circlemarker: { // Options for circle markers
                color: '#FF0000' // Red color for circle markers
            }
        }
    });
    map.addControl(drawControl); // Add the drawing control to the map

    // Handle the creation of new layers (e.g., when a user finishes drawing)
    map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer; // Get the created layer
        drawnItems.addLayer(layer); // Add the layer to the drawnItems group

        // Display coordinates if the new layer is a marker
        if (layer instanceof L.Marker) {
            displayMarkerCoordinates(layer);
        }

        // Display length if the new layer is a polyline
        if (layer instanceof L.Polyline) {
            displayPolylineLength(layer);
        }
    });

    // Handle the editing of existing layers
    map.on('draw:edited', function (event) {
        const layers = event.layers; // Get all edited layers
        layers.eachLayer(function (layer) {
            // Recalculate and display length if the edited layer is a polyline
            if (layer instanceof L.Polyline) {
                displayPolylineLength(layer);
            }
        });
    });

    // Set up the download button to export drawn features as GPX files
    document.getElementById('download-gpx').addEventListener('click', function () {
        downloadGPX(drawnItems); // Export the drawnItems FeatureGroup as a GPX file
    });
}

/**
 * Displays the coordinates of a marker on the map in a popup.
 *
 * When a marker is added to the map, this function retrieves its latitude and longitude,
 * formats them to 5 decimal places, and displays the coordinates in a popup bound to the marker.
 *
 * @param {L.Marker} marker - The Leaflet marker for which coordinates will be displayed.
 *
 * Features:
 * - Retrieves the geographical coordinates (latitude and longitude) of the marker.
 * - Formats the coordinates to five decimal places for precision.
 * - Creates a popup at the marker's location with the coordinate information.
 * - Binds the popup to the marker, allowing it to be reopened by clicking the marker.
 *
 * Example Usage:
 * ```javascript
 * const marker = L.marker([78.3, 16]).addTo(map);
 * displayMarkerCoordinates(marker);
 * ```
 */
function displayMarkerCoordinates(marker) {
    // Get the latitude and longitude of the marker
    const latlng = marker.getLatLng();

    // Format the coordinates and create popup content
    const popupContent = `Coordinates: ${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;

    // Create a popup and set its position and content
    const popup = L.popup()
        .setLatLng(latlng)       // Position the popup at the marker's location
        .setContent(popupContent) // Set the content to the formatted coordinates
        .openOn(map);            // Open the popup on the map

    // Bind the popup to the marker so it can be reopened later
    marker.bindPopup(popup);
}

/**
 * Calculates and displays the length of a polyline on the map in a popup.
 *
 * This function retrieves the coordinates of a polyline, calculates its total length,
 * and displays the length in kilometers as a popup at the center of the polyline's bounds.
 *
 * @param {L.Polyline} polyline - The Leaflet polyline for which the length will be calculated and displayed.
 *
 * Features:
 * - Retrieves all coordinate points of the polyline.
 * - Calculates the total length of the polyline in meters.
 * - Converts the length to kilometers and rounds it to two decimal places.
 * - Creates and positions a popup displaying the length information at the center of the polyline's bounds.
 * - Binds the popup to the polyline, allowing it to be reopened by interacting with the polyline.
 *
 * Example Usage:
 * ```javascript
 * const polyline = L.polyline([[78.3, 16], [78.4, 16.1]]).addTo(map);
 * displayPolylineLength(polyline);
 * ```
 */
function displayPolylineLength(polyline) {
    // Get all the coordinates (latitudes and longitudes) of the polyline
    const latlngs = polyline.getLatLngs();

    // Calculate the total length of the polyline in meters
    const length = calculateLength(latlngs);

    // Convert the length to kilometers and format it to two decimal places
    const lengthInKm = (length / 1000).toFixed(2);

    // Create a popup with the calculated length
    const popupContent = `Length: ${lengthInKm} km`;
    const popup = L.popup()
        .setLatLng(polyline.getBounds().getCenter()) // Position the popup at the polyline's center
        .setContent(popupContent)                   // Set the content to the length information
        .openOn(map);                               // Open the popup on the map

    // Bind the popup to the polyline so it can be reopened later
    polyline.bindPopup(popup);
}

/**
 * Calculates the total length of a series of coordinates.
 *
 * This function computes the cumulative distance between consecutive points
 * in an array of latitude and longitude coordinates. The distance between
 * each pair of points is calculated using the `distanceTo` method, which
 * utilizes the haversine formula to compute the great-circle distance.
 *
 * @param {Array<L.LatLng>} latlngs - An array of Leaflet `LatLng` objects representing the points.
 * @returns {number} The total length in meters as a floating-point number.
 *
 * Features:
 * - Iterates through an array of geographical points.
 * - Uses the `distanceTo` method to calculate distances between consecutive points.
 * - Returns the cumulative distance in meters.
 *
 * Example Usage:
 * ```javascript
 * const latlngs = [L.latLng(78.3, 16), L.latLng(78.4, 16.1), L.latLng(78.5, 16.2)];
 * const totalLength = calculateLength(latlngs); // Total length in meters
 * console.log(`Total Length: ${totalLength} meters`);
 * ```
 */
function calculateLength(latlngs) {
    let length = 0;

    // Iterate through the array of coordinates to calculate distances between points
    for (let i = 0; i < latlngs.length - 1; i++) {
        length += latlngs[i].distanceTo(latlngs[i + 1]); // Add the distance between consecutive points
    }

    return length; // Return the total length in meters
}

/**
 * Handles the upload and processing of GPX files, converting them to GeoJSON and displaying them on the map.
 *
 * This function allows users to upload GPX files, parses them into GeoJSON format,
 * filters the data to include only supported features (e.g., points and polylines),
 * and displays the resulting layers on the map. It also adjusts the map view to fit
 * the bounds of the uploaded data.
 *
 * @param {Event} event - The input event triggered by the file upload.
 *
 * Features:
 * - Processes multiple GPX files from the upload input.
 * - Converts GPX data to GeoJSON format using the Leaflet GPX plugin.
 * - Filters the GeoJSON data to include only specific geometry types (e.g., points and polylines).
 * - Adds the filtered data to the `drawnItems` layer group.
 * - Displays the length of polylines and adjusts the map view to the bounds of the uploaded data.
 *
 * Dependencies:
 * - Requires the Leaflet GPX plugin for parsing GPX files.
 *
 * Example Usage:
 * ```javascript
 * document.getElementById('upload-gpx').addEventListener('change', handleGPXUpload);
 * ```
 */
function handleGPXUpload(event) {
    // Get the list of uploaded files
    const files = event.target.files;

    // Process each file individually
    Array.from(files).forEach(file => {
        const reader = new FileReader(); // Create a FileReader instance

        // Event listener for when the file is read
        reader.onload = function (e) {
            const gpxData = e.target.result; // Get the GPX file content

            // Parse the GPX data into a Leaflet GPX layer
            const gpxLayer = new L.GPX(gpxData, { async: true })
                .on('loaded', function (e) {
                    // Convert the GPX data to GeoJSON format
                    const geojson = gpxLayer.toGeoJSON();

                    // Filter the GeoJSON to include only supported features
                    const filteredGeojson = filterGeoJSON(geojson);

                    // Clear existing layers if necessary
                    // drawnItems.clearLayers();

                    // Add the filtered GeoJSON data to the drawnItems layer group
                    L.geoJSON(filteredGeojson, {
                        onEachFeature: function (feature, layer) {
                            drawnItems.addLayer(layer); // Add the feature to the drawnItems group

                            // Display length if the feature is a polyline
                            if (feature.geometry.type === 'LineString') {
                                displayPolylineLength(layer);
                            }
                        }
                    });

                    // Adjust the map view to fit the bounds of the new data
                    const bounds = L.geoJSON(filteredGeojson).getBounds();
                    map.fitBounds(bounds); // Zoom and center the map to show all uploaded data
                });
        };

        // Read the file as text to process its content
        reader.readAsText(file);
    });
}

/**
 * Filters a GeoJSON object to include only specific geometry types: polylines (LineString) and points (Point).
 *
 * This function processes a GeoJSON object and removes any features that do not have a geometry type
 * of "LineString" or "Point." The filtered GeoJSON is returned as a new FeatureCollection.
 *
 * @param {Object} geojson - A GeoJSON object containing a collection of features.
 * @returns {Object} A filtered GeoJSON object containing only LineString and Point features.
 *
 * Features:
 * - Ensures that only supported geometry types (polylines and points) are included in the output.
 * - Returns a new GeoJSON FeatureCollection with the filtered features.
 *
 * Example Usage:
 * ```javascript
 * const geojson = {
 *     type: 'FeatureCollection',
 *     features: [
 *         { type: 'Feature', geometry: { type: 'LineString', coordinates: [[0, 0], [1, 1]] } },
 *         { type: 'Feature', geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 1], [1, 0], [0, 0]]] } },
 *         { type: 'Feature', geometry: { type: 'Point', coordinates: [0, 0] } }
 *     ]
 * };
 * const filteredGeoJSON = filterGeoJSON(geojson);
 * console.log(filteredGeoJSON);
 * // Output: A GeoJSON object containing only the LineString and Point features.
 * ```
 */
function filterGeoJSON(geojson) {
    // Filter the GeoJSON to include only polylines (LineString) and points (Point)
    return {
        type: 'FeatureCollection', // Ensure the return type is a FeatureCollection
        features: geojson.features.filter(feature =>
            feature.geometry.type === 'LineString' || feature.geometry.type === 'Point'
        ) // Include features only if their geometry type is LineString or Point
    };
}

/**
 * Exports a Leaflet layer group as a GPX file and triggers a download.
 *
 * This function converts a given Leaflet layer group (containing features like polylines and markers)
 * into a GeoJSON object, then transforms it into GPX format using the `togpx` library. It creates
 * a downloadable GPX file and triggers a browser download for the user.
 *
 * @param {L.LayerGroup} layerGroup - The Leaflet layer group to be exported and downloaded.
 *
 * Features:
 * - Converts the layer group to GeoJSON format using `toGeoJSON()`.
 * - Transforms the GeoJSON into GPX format using the `togpx` library.
 * - Creates a downloadable GPX file in the user's browser.
 * - Automatically names the file as `map-drawings.gpx`.
 *
 * Dependencies:
 * - Requires the `togpx` library to convert GeoJSON to GPX format.
 *
 * Example Usage:
 * ```javascript
 * const drawnItems = new L.FeatureGroup();
 * downloadGPX(drawnItems); // Downloads the features in `drawnItems` as a GPX file
 * ```
 */
function downloadGPX(layerGroup) {
    // Convert the layer group into a GeoJSON object
    const geojson = layerGroup.toGeoJSON();

    // Transform the GeoJSON object into GPX format
    const gpx = togpx(geojson);

    // Create a downloadable blob with the GPX data
    const blob = new Blob([gpx], { type: 'application/gpx+xml;charset=utf-8' });

    // Generate a URL for the blob
    const url = URL.createObjectURL(blob);

    // Create a temporary anchor element for triggering the download
    const a = document.createElement('a');
    a.href = url;                  // Set the blob URL as the anchor's href
    a.download = 'map-drawings.gpx'; // Set the default filename for the download

    // Append the anchor to the document body and simulate a click
    document.body.appendChild(a);
    a.click();

    // Remove the temporary anchor from the document
    document.body.removeChild(a);
}

async function loadVariablesConfig(variablesConfigUrl) {
    if (!configVariablesLoaded) {
        try {
            const response = await fetch(variablesConfigUrl);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            let configResponse = await response.json();
            configVariablesData = configResponse['variables']
            configVariablesLoaded = true;
            console.log("Configuration loaded");
            populateVariablesMenu(configVariablesData);
        } catch (error) {
            console.error("Failed to load configuration:", error);
        }
    } else {
        console.log("Configuration already loaded.");
    }
}
