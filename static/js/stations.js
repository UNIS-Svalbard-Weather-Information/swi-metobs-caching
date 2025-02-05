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
 * Array to store offline station data.
 * @type {Array.<Object>}
 */
let offlineStations = [];

/**
 * Object to store the visibility state for each station.
 * @type {Object.<string, boolean>}
 */
let stationVisibility = {};

/**
 * Loads both online and offline stations from the API and initializes the map controls.
 *
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function loadStations(windImagesUrl) {
    const onlineStationsUrl = "/api/station/online?type=all";
    const offlineStationsUrl = "/api/station/offline?type=all";

    Promise.all([
        fetch(onlineStationsUrl).then(response => response.json()),
        fetch(offlineStationsUrl).then(response => response.json())
    ])
    .then(([onlineData, offlineData]) => {
        // Ensure responses contain valid station lists
        const onlineStations = onlineData.online_stations || [];
        const offlineStationsList = offlineData.online_stations || [];

        // Separate online stations into fixed and mobile categories
        mobileStations = onlineStations.filter(station => station.type === "mobile");
        fixedStations = onlineStations.filter(station => station.type === "fixed");

        // Assign offline stations separately
        offlineStations = offlineStationsList;

        // Initialize visibility state (only online stations are visible by default)
        onlineStations.forEach(station => stationVisibility[station.id] = true);
        offlineStations.forEach(station => stationVisibility[station.id] = false);

        // Initialize UI with both online and offline stations
        initializeProjectControls(windImagesUrl);
        initializeEventListeners(windImagesUrl);

        // Fetch initial parameters and update station data
        const initialDuration = parseInt(document.getElementById('track-duration-select').value, 10);
        const initialVariable = document.getElementById('variable-select-dropdown').value;
        updateStationsData(initialDuration, windImagesUrl, initialVariable);
    })
    .catch(error => {
        console.error("Error loading stations:", error);
    });
}


/**
 * Initializes the project controls UI with checkboxes for each station.
 *
 * @param {string} windImagesUrl - Base URL for wind images.
 */

function initializeProjectControls(windImagesUrl) {
    const projectControls = document.getElementById('project-controls');
    projectControls.innerHTML = ""; // Clear existing UI before adding new elements

    const projects = {};

    // Collect all stations (online and offline)
    const allStations = [...mobileStations, ...fixedStations, ...offlineStations];

    allStations.forEach(station => {
        const project = station.project || 'Uncategorized';
        if (!projects[project]) {
            projects[project] = [];
        }
        projects[project].push(station);
    });

    // Create UI elements for each project
    for (const project in projects) {
        const projectDiv = document.createElement('div');
        projectDiv.classList.add('project-item');

        const projectHeader = document.createElement('div');
        projectHeader.classList.add('project-header');

        // Master checkbox for the project
        const projectCheckbox = document.createElement('input');
        projectCheckbox.type = 'checkbox';
        projectCheckbox.id = `project-${project}`;
        projectCheckbox.checked = true;
        projectCheckbox.addEventListener('change', () => {
            toggleProjectStations(project, projectCheckbox.checked, windImagesUrl);
        });

        const projectLabel = document.createElement('button');
        projectLabel.classList.add('project-toggle-button');
        projectLabel.textContent = project;
        projectLabel.onclick = function () {
            const content = this.parentNode.parentNode.querySelector('.station-list');
            content.style.display = content.style.display === 'block' ? 'none' : 'block';
        };

        // Styling the button
        projectLabel.style.marginLeft = '10px';

        // Adding master checkbox and button to project header
        projectHeader.appendChild(projectCheckbox);
        projectHeader.appendChild(projectLabel);

        const stationListDiv = document.createElement('div');
        stationListDiv.classList.add('station-list');
        stationListDiv.style.display = 'none'; // Initially hidden

        // Create UI for each station within the project
        projects[project].forEach(station => {
            const stationDiv = document.createElement('div');
            stationDiv.classList.add('station-item');
            stationDiv.id = `station-${station.id}`;

            const stationCheckbox = document.createElement('input');
            stationCheckbox.type = 'checkbox';
            stationCheckbox.checked = station.status === "online"; // Checked only if online
            stationCheckbox.disabled = station.status === "offline"; // Disable checkbox for offline stations
            stationCheckbox.addEventListener('change', () => {
                toggleStation(station.id, stationCheckbox.checked, windImagesUrl);
            });

            const stationLabel = document.createElement('label');
            stationLabel.setAttribute('for', `station-${station.id}`);
            stationLabel.textContent = station.name;

            if (station.status === "offline") {
                // Apply strikethrough and grey color for offline stations
                stationLabel.style.textDecoration = "line-through";
                stationLabel.style.color = "grey";
            }

            stationDiv.appendChild(stationCheckbox);
            stationDiv.appendChild(stationLabel);
            stationListDiv.appendChild(stationDiv);
        });

        // Append the header and station list to the project div
        projectDiv.appendChild(projectHeader);
        projectDiv.appendChild(stationListDiv);
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
        if (stationVisibility[station.id]) {
            updateMobileStationData(station, duration, windImagesUrl, variable);
        }
    });
    fixedStations.forEach(station => {
        if (stationVisibility[station.id]) {
            updateFixedStationData(station, windImagesUrl);
        }
    });
}

/**
 * Fetches data for a specific mobile station.
 * 
 * @param {Object} station - The mobile station data.
 * @param {number} duration - The duration for which to fetch the data.
 * @returns {Promise<Object|null>} - A promise that resolves to the station data or null in case of error.
 */
async function fetchMobileStationData(station, duration) {
    try {
        const response = await fetch(`/api/mobile-station-data/${station.id}?duration=${duration}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        const data = await response.json();
        console.log('Fetch successful:', data);  // Log the successful data
        return data;
    } catch (error) {
        //console.error('Error fetching mobile station data:', error);
        updateStationUIOnError(station.id);
        return null;
    }
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
            //console.error('Error fetching mobile station data:', error);
            updateStationUIOnError(station.id); 
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
    stationVisibility[stationId] = isVisible;
    
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

function toggleProjectStations(project, isVisible, windImagesUrl) {
    const allStations = [...mobileStations, ...fixedStations];
    allStations.forEach(station => {
        if (station.project === project) {
            const stationCheckbox = document.getElementById(`station-${station.id}`);
            stationCheckbox.checked = isVisible;
            toggleStation(station.id, isVisible, windImagesUrl);
        }
    });
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

                console.log(colorScale)

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
                updateColorBar(variable, extendedMinValue, extendedMaxValue, colorScale);
            }
        }, null);
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
    const iconUrl = getWindSpeedIcon(windImagesUrl, data.windSpeed, data.windDirection);
    
    const windRotatedIcon = L.divIcon({
        className: 'custom-icon',
        html: `<img src="${iconUrl}" width="80" height="80" class="rotated-icon"  style="transform: rotate(${data.windDirection + 90}deg);" />`,
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
 * @param {number} windSpeed - The wind speed in meters per second.
 * @param {number} windDirection - The wind direction value.
 * @returns {string} - The URL of the wind speed icon.
 */
function getWindSpeedIcon(basePath, windSpeed, windDirection) {
    if (typeof basePath !== 'string' || basePath.trim() === '') {
        throw new Error('Invalid base path');
    }
    if (windSpeed == null || windDirection == null ||
        typeof windSpeed !== 'number' || typeof windDirection !== 'number') {
        return `${basePath}/null.gif`;
    }

    // Convert wind speed from m/s to knots
    const windSpeedKts = windSpeed * 1.94384;

    // Predefined wind speeds in knots
    const windSpeeds = [0, 5, 10, 15, 20, 25, 30, 35, 50, 55, 60, 65, 100, 105];
    const closest = windSpeeds.reduce((prev, curr) =>
        Math.abs(curr - windSpeedKts) < Math.abs(prev - windSpeedKts) ? curr : prev
    );

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

function updateStationUIOnError(stationId) {
    const stationElement = document.getElementById(`station-${stationId}`);
    if (stationElement) {
        stationElement.style.textDecoration = "line-through";
        stationElement.style.color = "grey";
        const parent = stationElement.parentElement;
        parent.appendChild(stationElement); // Move to the end of the list
    }
}
