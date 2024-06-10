/**
 * Object to store track layers for each station.
 * @type {Object.<string, L.Layer[]>}
 */
let trackLayers = {};

/**
 * Object to store boat markers for each station.
 * @type {Object.<string, L.Marker>}
 */
let boatMarkers = {};

/**
 * Object to store fixed station markers.
 * @type {Object.<string, L.Marker>}
 */
let fixedStationMarkers = {};

/**
 * Object to store wind markers for each station.
 * @type {Object.<string, L.Marker>}
 */
let windMarkers = {};

/**
 * Array to store mobile station data.
 * @type {Array.<Object>}
 */
let mobileStations = [];

/**
 * Array to store fixed station data.
 * @type {Array.<Object>}
 */
let fixedStations = [];

/**
 * Loads station data from provided URLs and initializes the map controls.
 * 
 * @param {string} mobileStationConfigUrl - URL to fetch mobile station configuration.
 * @param {string} fixedStationConfigUrl - URL to fetch fixed station configuration.
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function loadStations(mobileStationConfigUrl, fixedStationConfigUrl, windImagesUrl) {
    Promise.all([
        fetch(mobileStationConfigUrl).then(response => response.json()),
        fetch(fixedStationConfigUrl).then(response => response.json())
    ])
    .then(([mobileStationsData, fixedStationsData]) => {
        mobileStations = mobileStationsData;
        fixedStations = fixedStationsData;

        initializeProjectControls(windImagesUrl);
        initializeEventListeners(windImagesUrl);

        const initialDuration = parseInt(document.getElementById('track-duration-select').value, 10);
        const initialVariable = document.getElementById('variable-select-dropdown').value;
        updateStationsData(initialDuration, windImagesUrl, initialVariable);
    })
    .catch(error => {
        console.error('Error loading stations:', error);
    });
}

/**
 * Initializes the project controls UI with checkboxes for each station.
 * 
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function initializeProjectControls(windImagesUrl) {
    const projectControls = document.getElementById('project-controls');
    const projects = {};

    const allStations = [...mobileStations, ...fixedStations];

    allStations.forEach(station => {
        const project = station.project || 'Uncategorized';
        if (!projects[project]) {
            projects[project] = [];
        }
        projects[project].push(station);
    });

    for (const project in projects) {
        const projectDiv = document.createElement('div');
        const projectLabel = document.createElement('h3');
        projectLabel.textContent = project;
        projectDiv.appendChild(projectLabel);

        projects[project].forEach(station => {
            const stationDiv = document.createElement('div');
            stationDiv.classList.add('station-item'); // Add this line

            const stationCheckbox = document.createElement('input');
            stationCheckbox.type = 'checkbox';
            stationCheckbox.id = `station-${station.id}`;
            stationCheckbox.checked = true;
            stationCheckbox.addEventListener('change', () => {
                toggleStation(station.id, stationCheckbox.checked, windImagesUrl);
            });

            const stationLabel = document.createElement('label');
            stationLabel.setAttribute('for', `station-${station.id}`);
            stationLabel.textContent = station.name;

            stationDiv.appendChild(stationCheckbox);
            stationDiv.appendChild(stationLabel);
            projectDiv.appendChild(stationDiv);
        });

        projectControls.appendChild(projectDiv);
    }
}

/**
 * Initializes event listeners for track duration and variable selection changes.
 * 
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function initializeEventListeners(windImagesUrl) {
    const durationSelect = document.getElementById('track-duration-select');
    const variableSelect = document.getElementById('variable-select-dropdown');
    
    durationSelect.addEventListener('change', () => {
        const duration = parseInt(durationSelect.value, 10);
        const variable = variableSelect.value;
        updateStationsData(duration, windImagesUrl, variable);
    });

    variableSelect.addEventListener('change', () => {
        const duration = parseInt(durationSelect.value, 10);
        const variable = variableSelect.value;
        updateStationsData(duration, windImagesUrl, variable);
    });
}

/**
 * Fetches and updates data for all stations based on selected duration and variable.
 * 
 * @param {number} duration - The duration for which to fetch the data.
 * @param {string} windImagesUrl - Base URL for wind images.
 * @param {string} variable - The variable to display.
 */
function updateStationsData(duration, windImagesUrl, variable) {
    mobileStations.forEach(station => {
        updateMobileStationData(station, duration, windImagesUrl, variable);
    });
    fixedStations.forEach(station => {
        updateFixedStationData(station, windImagesUrl);
    });
}

/**
 * Fetches data for a specific mobile station.
 * 
 * @param {Object} station - The mobile station data.
 * @param {number} duration - The duration for which to fetch the data.
 * @returns {Promise<Object|null>} - A promise that resolves to the station data or null in case of error.
 */
function fetchMobileStationData(station, duration) {
    return fetch(`/api/mobile-station-data/${station.id}?duration=${duration}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error fetching mobile station data:', error);
            return null;
        });
}

/**
 * Fetches data for a specific fixed station.
 * 
 * @param {Object} station - The fixed station id.
 * @param {number} duration - The duration for which to fetch the data.
 * @returns {Promise<Object|null>} - A promise that resolves to the station data or null in case of error.
 */
function fetchFixedStationData(station, duration) {
    return fetch(`/api/fixed-station-data/${station.id}?duration=${duration}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error fetching mobile station data:', error);
            return null;
        });
}

/**
 * Toggles the visibility of a station's data on the map.
 * 
 * @param {string} stationId - The ID of the station.
 * @param {boolean} isVisible - Whether the station data should be visible.
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function toggleStation(stationId, isVisible, windImagesUrl) {
    if (!isVisible) {
        if (trackLayers[stationId]) {
            trackLayers[stationId].forEach(layer => map.removeLayer(layer));
            delete trackLayers[stationId];
        }
        if (boatMarkers[stationId]) {
            map.removeLayer(boatMarkers[stationId]);
            delete boatMarkers[stationId];
        }
        if (windMarkers[stationId]) {
            map.removeLayer(windMarkers[stationId]);
            delete windMarkers[stationId];
        }
        if (fixedStationMarkers[stationId]) {
            map.removeLayer(fixedStationMarkers[stationId]);
            delete fixedStationMarkers[stationId];
        }
    } else {
        const durationSelect = document.getElementById('track-duration-select');
        const variableSelect = document.getElementById('variable-select-dropdown');
        const duration = parseInt(durationSelect.value, 10);
        const variable = variableSelect.value;
        
        const station = mobileStations.find(s => s.id === stationId);

        if (station) {
            updateMobileStationData(station, duration, windImagesUrl, variable);
        } else {
            const fixedStation = fixedStations.find(s => s.id === stationId);
            if (fixedStation) {
                updateFixedStationData(fixedStation, windImagesUrl);
            } else {
                console.error(`Station with id ${stationId} not found in both mobile and fixed stations`);
            }
        }
    }
}

/**
 * Updates the data for a specific mobile station and displays it on the map.
 * 
 * @param {Object} station - The mobile station data.
 * @param {number} duration - The duration for which to fetch the data.
 * @param {string} windImagesUrl - Base URL for wind images.
 * @param {string} variable - The variable to display.
 */
function updateMobileStationData(station, duration, windImagesUrl, variable) {
    if (trackLayers[station.id]) {
        trackLayers[station.id].forEach(layer => map.removeLayer(layer));
        delete trackLayers[station.id];
    }

    if (duration === 0) {
        // No track to display, but show the boat icon
        fetchMobileStationData(station, duration)
            .then(data => {
                if (data) {
                    updateBoatMarker(station, data, variable);
                    updateWindMarker(station, data, windImagesUrl);
                }
            });
        return;
    }

    fetchMobileStationData(station, duration)
        .then(data => {
            if (data) {
                updateBoatMarker(station, data, variable);
                updateWindMarker(station, data, windImagesUrl);

                const latlngs = data.track.map(dp => [dp.lat, dp.lon]);
                const values = data.track.map(dp => dp.variable[variable]);
                const filteredValues = values.filter(v => v !== null && v !== undefined);
                if (filteredValues.length === 0) return;

                const minValue = Math.min(...filteredValues);
                const maxValue = Math.max(...filteredValues);
                const extendedMinValue = minValue - (0.1 * minValue);
                const extendedMaxValue = maxValue + (0.1 * maxValue);

                const colorScale = getColorScale(variable, extendedMinValue, extendedMaxValue);

                let segments = [];
                for (let i = 0; i < latlngs.length - 1; i++) {
                    const segment = L.polyline([latlngs[i], latlngs[i + 1]], {
                        color: colorScale(values[i]),
                        weight: 5,
                        opacity: 0.7
                    }).addTo(map);
                    segments.push(segment);

                    // Add popups to each point
                    const dot = L.circleMarker(latlngs[i], {
                        radius: 5,
                        color: colorScale(values[i]),
                        fillColor: colorScale(values[i]),
                        fillOpacity: 0.9
                    })
                    .bindPopup(createPopupContent(station, data.track[i].variable))
                    .addTo(map);

                    segments.push(dot);
                }

                trackLayers[station.id] = segments;
                updateColorBar(variable, extendedMinValue, extendedMaxValue);
            }
        });
}

/**
 * Updates the marker for a fixed station.
 * 
 * @param {Object} station - The fixed station data.
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function updateFixedStationData(station, windImagesUrl) {
    if (trackLayers[station.id]) {
        trackLayers[station.id].forEach(layer => map.removeLayer(layer));
        delete trackLayers[station.id];
    }


    fetchFixedStationData(station, 0)
        .then(data => {
            if (data) {
                updateFixedStationMarker(station, data);
                updateWindMarker(station, data, windImagesUrl);
            }
        });
    return;
    
}

/**
 * Creates the popup content for a station.
 * 
 * @param {string} stationName - The name of the station.
 * @param {Object} dataPoint - The data point to display.
 * @returns {string} - The HTML content for the popup.
 */
function createPopupContent(station, dataPoint) {
    const date = new Date(dataPoint.time * 1000);
    const dateString = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    const windDirectionLetter = getWindDirectionLetter(dataPoint.windDirection);

    const variables = station.variables;
    let content = `<strong>${station.name}</strong><br>${dateString}<br>----<br>`;

    if (variables.airTemperature) {
        content += `Air Temperature: ${dataPoint.airTemperature !== null && dataPoint.airTemperature !== undefined ? dataPoint.airTemperature.toFixed(2) : 'N/A'} °C<br>`;
    }

    if (variables.seaSurfaceTemperature) {
        content += `Sea Surface Temperature: ${dataPoint.seaSurfaceTemperature !== null && dataPoint.seaSurfaceTemperature !== undefined ? dataPoint.seaSurfaceTemperature.toFixed(2) : 'N/A'} °C<br>`;
    }

    if (variables.windSpeed) {
        content += `Wind Speed: ${dataPoint.windSpeed !== null && dataPoint.windSpeed !== undefined ? dataPoint.windSpeed.toFixed(2) : 'N/A'} m/s<br>`;
    }

    if (variables.windDirection) {
        content += `Wind Direction: ${dataPoint.windDirection !== null && dataPoint.windDirection !== undefined ? `${dataPoint.windDirection.toFixed(2)}° (${windDirectionLetter})` : 'N/A'}<br>`;
    }

    if (variables.relativeHumidity) {
        content += `Relative Humidity: ${dataPoint.relativeHumidity !== null && dataPoint.relativeHumidity !== undefined ? dataPoint.relativeHumidity.toFixed(2) : 'N/A'} %`;
    }

    return content;
}


/**
 * Converts wind direction in degrees to a compass direction letter.
 * 
 * @param {number} degrees - The wind direction in degrees.
 * @returns {string} - The corresponding compass direction letter.
 */
function getWindDirectionLetter(degrees) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(degrees / 45) % 8;
    return directions[index];
}

/**
 * Updates the boat marker for a mobile station.
 * 
 * @param {Object} station - The mobile station data.
 * @param {Object} data - The data to display.
 * @param {string} variable - The variable to display.
 */
function updateBoatMarker(station, data, variable) {
    const boatIcon = L.divIcon({
        className: 'boat-marker',
        html: `<img src="${station.icon}" width="32" height="32"/>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    if (boatMarkers[station.id]) {
        map.removeLayer(boatMarkers[station.id]);
    }

    const variableInfo = createPopupContent(station, data.latest);
    const boatMarker = L.marker([data.lat, data.lon], { icon: boatIcon }).addTo(map);
    boatMarker.bindPopup(variableInfo);
    boatMarkers[station.id] = boatMarker;
}

/**
 * Updates the marker for a fixed station.
 * 
 * @param {Object} station - The fixed station data.
 * @param {Object|null} data - The data to display.
 */
function updateFixedStationMarker(station, data) {
    const Icon = L.icon({
        iconUrl: station.icon,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    if (fixedStationMarkers[station.id]) {
        map.removeLayer(fixedStationMarkers[station.id]);
    }

    const variableInfo = createPopupContent(station, data.latest);

    const Marker = L.marker([station.lat, station.lon], { icon: Icon }).addTo(map);
    Marker.bindPopup(variableInfo);
    fixedStationMarkers[station.id] = Marker;
}

/**
 * Updates the wind marker for a station.
 * 
 * @param {Object} station - The station data.
 * @param {Object} data - The data to display.
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function updateWindMarker(station, data, windImagesUrl) {
    const iconUrl = getWindSpeedIcon(windImagesUrl, data.windSpeed);
    
    const windRotatedIcon = L.divIcon({
        className: 'custom-icon',
        html: `<img src="${iconUrl}" width="80" height="80" class="rotated-icon"  style="transform: rotate(${data.windDirection - 90}deg);" />`,
        iconSize: [80, 80],
        iconAnchor: [40, 40]
    });

    if (windMarkers[station.id]) {
        map.removeLayer(windMarkers[station.id]);
    }

    const windMarker = L.marker([data.lat, data.lon], { 
        icon: windRotatedIcon,
    }).addTo(map);

    windMarker.bindPopup(createPopupContent(station, data.latest));
    windMarkers[station.id] = windMarker;
}

/**
 * Gets the appropriate wind speed icon based on wind speed.
 * 
 * @param {string} basePath - The base path for wind images.
 * @param {number} windSpeed - The wind speed value.
 * @returns {string} - The URL of the wind speed icon.
 */
function getWindSpeedIcon(basePath, windSpeed) {
    const windSpeeds = [0, 5, 10, 15, 20, 25, 30, 35, 50, 55, 60, 65, 100, 105];
    let closest = windSpeeds.reduce((prev, curr) => Math.abs(curr - windSpeed) < Math.abs(prev - windSpeed) ? curr : prev);
    return `${basePath}/${closest.toString().padStart(2, '0')}kts.gif`;
}

/**
 * Gets the color scale based on the variable and its min/max values.
 * 
 * @param {string} variable - The variable to display.
 * @param {number} minValue - The minimum value for the color scale.
 * @param {number} maxValue - The maximum value for the color scale.
 * @returns {Function} - A D3 color scale function.
 */
function getColorScale(variable, minValue, maxValue) {
    const colorScale = {
        "airTemperature": d3.scaleSequential(d3.interpolateCool).domain([minValue, maxValue]),
        "seaSurfaceTemperature": d3.scaleSequential(d3.interpolateCool).domain([minValue, maxValue]),
        "windSpeed": d3.scaleSequential(d3.interpolateBlues).domain([minValue, maxValue]),
        "windDirection": d3.scaleSequential(d3.interpolateRainbow).domain([minValue, maxValue]),
        "relativeHumidity": d3.scaleSequential(d3.interpolateViridis).domain([minValue, maxValue])
    };

    return colorScale[variable];
}
