let forecast = false; // Set to true to enable forecast, false to disable

/**
 * Object to store track layers for each station.
 * @type {Object.<string, L.Layer[]>}
 */
let trackLayers = {};

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
        const onlineStations = onlineData.online_stations || [];
        offlineStations = offlineData.offline_stations || [];

        fixedStations = onlineStations.filter(station => station.type === "fixed");

        onlineStations.forEach(station => stationVisibility[station.id] = true);
        offlineStations.forEach(station => stationVisibility[station.id] = false);

        initializeProjectControls(windImagesUrl);
        initializeEventListeners(windImagesUrl);

        const initialDuration = parseInt(document.getElementById('track-duration-select').getAttribute('value'), 10) || 0;
        const initialVariable = document.getElementById('variable-select-dropdown').value;
        //console.log(`Initial load - Duration: ${initialDuration}, Variable: ${initialVariable}`); // Debugging line
        updateStationsData(initialDuration, windImagesUrl, initialVariable);

        setInterval(() => {
            const duration = parseInt(document.getElementById('track-duration-select').getAttribute('value'), 10) || 0;
            const variable = document.getElementById('variable-select-dropdown').value;
            updateStationsData(duration, windImagesUrl, variable);
        }, 60000); // Auto update stations every minute
    })
    .catch(error => {
        console.error("Error loading stations:", error);
    });
}

function populateVariablesMenu(variables){
            const selectDropdown = document.getElementById('variable-select-dropdown');

            // Add a "None" option
            const noneOption = document.createElement('option');
            noneOption.value = '';
            noneOption.textContent = 'None';
            selectDropdown.appendChild(noneOption);

            // Populate the dropdown with variable names
            for (const variable in variables) {
                if (variables.hasOwnProperty(variable)) {
                    const option = document.createElement('option');
                    option.value = variable;
                    option.textContent = variables[variable].name;
                    selectDropdown.appendChild(option);
                }
            }

            // Set the default selected variable
            const defaultVariable = Object.keys(variables).find(key => variables[key].default);
            if (defaultVariable) {
                selectDropdown.value = defaultVariable;
            }

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
    const allStations = [...fixedStations, ...offlineStations];

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
    const variableSelect = document.getElementById('variable-select-dropdown');
    const trackDurationSelect = document.getElementById('track-duration-select');

    // Ensure track-duration-select has a default value
    if (!trackDurationSelect.getAttribute('value')) {
        trackDurationSelect.setAttribute('value', '0');
    }

    variableSelect.addEventListener('change', () => {
        const duration = parseInt(trackDurationSelect.getAttribute('value'), 10) || 0;
        const variable = variableSelect.value;
        //console.log(`Variable changed - Duration: ${duration}, Variable: ${variable}`); // Debugging line
        updateStationsData(duration, windImagesUrl, variable);
    });

    trackDurationSelect.addEventListener('change', () => {
        const duration = parseInt(trackDurationSelect.getAttribute('value'), 10) || 0;
        const variable = variableSelect.value;
        //console.log(`Duration changed - Duration: ${duration}, Variable: ${variable}`); // Debugging line
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
    fixedStations.forEach(station => {
        if (stationVisibility[station.id]) {
            updateFixedStationData(station, windImagesUrl, duration);
        }
    });
}

/**
 * Fetches data for a specific station.
 *
 * @param {Object} station - The station object containing its ID.
 * @param {number} duration - The duration for which to fetch the data.
 * @returns {Promise<Object|null>} - A promise that resolves to the station data or null in case of an error.
 */
function fetchStationData(station, duration) {
    return fetch(`/api/station-data/${station.id}?data=${duration}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error(`Error fetching data for station ${station.id}:`, error);
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
        if (fixedStationMarkers[stationId]) {
            map.removeLayer(fixedStationMarkers[stationId]);
            delete fixedStationMarkers[stationId];
        }
        if (windMarkers[stationId]) {
            map.removeLayer(windMarkers[stationId]);
            delete windMarkers[stationId];
        }
    } else {
        const fixedStation = fixedStations.find(s => s.id === stationId);
        if (fixedStation) {
            const duration = parseInt(document.getElementById('track-duration-select').getAttribute('value'), 10);
            updateFixedStationData(fixedStation, windImagesUrl, duration);
        } else {
            console.error(`Station with id ${stationId} not found in fixed stations`);
        }
    }
}

function toggleProjectStations(project, isVisible, windImagesUrl) {
    const allStations = [...fixedStations];
    allStations.forEach(station => {
        if (station.project === project) {
            const stationCheckbox = document.getElementById(`station-${station.id}`);
            stationCheckbox.checked = isVisible;
            toggleStation(station.id, isVisible, windImagesUrl);
        }
    });
}

/**
 * Updates the marker for a fixed station.
 *
 * @param {Object} station - The fixed station data.
 * @param {string} windImagesUrl - Base URL for wind images.
 * @param {number} duration - The duration for which to fetch the data.
 */
function updateFixedStationData(station, windImagesUrl, duration) {
    if (trackLayers[station.id]) {
        trackLayers[station.id].forEach(layer => map.removeLayer(layer));
        delete trackLayers[station.id];
    }

    fetchStationData(station, duration)
        .then(data => {
            if (data) {
                updateFixedStationMarker(station, data, windImagesUrl);
            }
        });
}

/**
 * Creates the popup content for a station.
 *
 * @param {Object} station - The station object containing metadata.
 * @param {Object|null} dataPoint - The latest measurement from the timeseries.
 * @returns {string} - The HTML content for the popup.
 */
function createPopupContent(station, dataPoint) {
    if (!dataPoint) {
        return `<strong>${station.name}</strong><br>No recent data available.`;
    }

    // Convert timestamp to a readable format
    const date = new Date(dataPoint.timestamp);
    const dateString = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    const windDirectionLetter = dataPoint.windDirection !== undefined
        ? getWindDirectionLetter(dataPoint.windDirection)
        : 'N/A';

    // Available variables in the station metadata
    const variables = station.variables || [];

    let content = `<strong>${station.name}</strong><br>${dateString}<br>----<br>`;

    // Iterate over the config variables
    for (const [key, variableConfig] of Object.entries(configVariablesData)) {
        if (variables.includes(key)) {
            const value = dataPoint[key] !== null && dataPoint[key] !== undefined ? dataPoint[key].toFixed(2) : 'N/A';
            let displayValue = value;

            // Append wind direction letter if applicable
            if (key === 'windDirection' && windDirectionLetter !== 'N/A') {
                displayValue += `° (${windDirectionLetter})`;
            }

            content += `${variableConfig.name}: ${displayValue} ${variableConfig.unit}<br>`;
        }
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
 * Updates the marker for a fixed station using the new API format.
 *
 * @param {Object} station - The fixed station data.
 * @param {Object|null} data - The station data, containing timeseries measurements.
 */
function updateFixedStationMarker(station, data, windImagesUrl) {

    // Get the selected variable name from the dropdown
    const selectedVariableName = document.getElementById('variable-select-dropdown').value;
    let variableValue = 'N/A';
    let unit = '';

    // Find the selected variable configuration
    const selectedVariableConfig = configVariablesData[selectedVariableName];

    // Extract the latest available data from timeseries
    const latestData = (data && data.timeseries && data.timeseries.length > 0)
        ? data.timeseries[0] // Get the most recent measurement
        : null;

    if (selectedVariableConfig && latestData) {
        unit = selectedVariableConfig.unit;
        variableValue = latestData[selectedVariableName];
    }

    // Create a custom icon with the marker image and text
    const customIcon = L.divIcon({
        className: 'custom-icon',
        html: `
        <div style="text-align: center;">
            <img src="${station.icon}" style="width: 32px; height: 32px; display: block; margin: 0 auto;" />
            ${selectedVariableName && variableValue !== undefined && unit ? `
            <div style="margin-top: 2px;">
                <span style="background-color: rgba(255, 255, 255, 0.6); padding: 2px 5px; border-radius: 3px;">
                    ${variableValue} ${unit}
                </span>
            </div>` : ''}
        </div>
        `,
        iconSize: [60, 32], // Adjust size as needed
        iconAnchor: [30, 16] // Adjust anchor as needed
    });

    // Remove existing marker if it exists
    if (fixedStationMarkers[station.id]) {
        map.removeLayer(fixedStationMarkers[station.id]);
    }

    // Create popup content using latest data
    const variableInfo = createPopupContent(station, latestData);

    // Add the marker to the map with the custom icon
    const marker = L.marker([station.location.lat, station.location.lon], { icon: customIcon }).addTo(map);
    marker.bindPopup(variableInfo);
    fixedStationMarkers[station.id] = marker;

    updateWindMarker(station, data, windImagesUrl);
}



/**
 * Updates the wind marker for a station using the new API format.
 *
 * @param {Object} station - The station data.
 * @param {Object|null} data - The station data, containing timeseries measurements.
 * @param {string} windImagesUrl - Base URL for wind images.
 */
function updateWindMarker(station, data, windImagesUrl) {
    // Extract the latest available data from timeseries
    const latestData = (data && data.timeseries && data.timeseries.length > 0)
        ? data.timeseries[0] // Get the most recent measurement
        : null;

    if (!latestData) {
        console.warn(`No wind data available for station ${station.id}`);
        return; // Exit function if there's no valid data
    }

    // Get wind speed and direction from the latest data
    const windSpeed = latestData.windSpeed;
    const windDirection = latestData.windDirection;

    // Generate wind icon URL based on speed & direction
    const iconUrl = getWindSpeedIcon(windImagesUrl, windSpeed, windDirection);

    // Create a rotated wind icon
    const windRotatedIcon = L.divIcon({
        className: 'custom-icon',
        html: `<img src="${iconUrl}" width="80" height="80" class="rotated-icon"
               style="transform: rotate(${windDirection + 90}deg);" />`,
        iconSize: [80, 80],
        iconAnchor: [40, 40]
    });

    // Remove existing wind marker if it exists
    if (windMarkers[station.id]) {
        map.removeLayer(windMarkers[station.id]);
    }

    // Add new wind marker with updated position and icon
    const windMarker = L.marker([station.location.lat, station.location.lon], {
        icon: windRotatedIcon,
    }).addTo(map);

    // Attach popup with latest data
    windMarker.bindPopup(createPopupContent(station, latestData));
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


// Function to update the timeline and cursor position
function updateTimeline() {
  const now = new Date();
  const hoursFromNow = parseInt(document.getElementById('track-duration-select').getAttribute('value'), 10) || 0;
  const timelineWidth = document.querySelector('.timeline').offsetWidth;

  // Calculate the position of the cursor relative to the center
  const cursorPosition = ((hoursFromNow / 48) * timelineWidth) + (timelineWidth / 2);

  // Check if forecast is disabled and hoursFromNow is in the future
  if (!forecast && hoursFromNow > 0) {
    alert("Forecast is not available.");
    // Reset cursor to the current time
    document.getElementById('track-duration-select').style.left = `${timelineWidth / 2}px`;
    document.getElementById('track-duration-select').setAttribute('value', '0');
    return;
  }

  document.getElementById('track-duration-select').style.left = `${cursorPosition}px`;

  // Calculate the current hour of the day (0-23)
  const currentHour = now.getHours();

  // Calculate the flex values for each day
  const dayMinusFlex = (24 - currentHour) / 48;
  const dayCenterFlex = 24 / 48;
  const dayPlusFlex = currentHour / 48;

  // Apply the flex values to the day elements
  const dayMinus = document.getElementById('day-minus');
  const dayCenter = document.getElementById('day-center');
  const dayPlus = document.getElementById('day-plus');

  dayMinus.style.flex = dayMinusFlex;
  dayCenter.style.flex = dayCenterFlex;
  dayPlus.style.flex = dayPlusFlex;

  // Update the day labels
  const dayMinusDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const dayPlusDate = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  const dayCenterDate = new Date(now.getTime());

  dayMinus.textContent = dayMinusDate.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
  dayPlus.textContent = dayPlusDate.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
  dayCenter.textContent = dayCenterDate.toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase();

  // Update the duration display and tooltip
  const tooltip = document.getElementById('tooltip');
  if (hoursFromNow === 0) {
    tooltip.textContent = "Now";
  } else {
    const shiftedTime = new Date(now.getTime() + hoursFromNow * 60 * 60 * 1000);
    tooltip.textContent = `${shiftedTime.getHours().toString().padStart(2, '0')}:00`;
  }

  // Remove existing hour ticks and day bars
  const existingTicks = document.querySelectorAll('.hour-tick, .day-bar');
  existingTicks.forEach(tick => tick.remove());

  // Create hour ticks
  const timeline = document.querySelector('.timeline');
  for (let i = 0; i < 49; i++) {
    const tick = document.createElement('div');
    tick.classList.add('hour-tick');
    tick.style.left = `${(i / 48) * 100}%`;
    timeline.appendChild(tick);
  }

  // Calculate and create day bars
  const dayBars = [
    { element: dayMinus, position: dayMinusFlex },
    { element: dayCenter, position: dayMinusFlex + dayCenterFlex },
    { element: dayPlus, position: dayMinusFlex + dayCenterFlex + dayPlusFlex }
  ];

  dayBars.forEach(({ element, position }) => {
    const dayBar = document.createElement('div');
    dayBar.classList.add('day-bar');
    dayBar.style.left = `${position * 100}%`;
    timeline.appendChild(dayBar);
  });
}

// Initialize the timeline
updateTimeline();

// Add event listeners to update the timeline when the cursor is dragged
const cursor = document.getElementById('track-duration-select');
let isDragging = false;
let startX;
let startLeft;

const handleMouseDown = (e) => {
  isDragging = true;
  startX = e.clientX || e.touches[0].clientX;
  startLeft = parseInt(window.getComputedStyle(cursor).left, 10);
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('touchmove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
  document.addEventListener('touchend', handleMouseUp);
};

const handleMouseMove = (e) => {
  if (!isDragging) return;
  const x = e.clientX || e.touches[0].clientX;
  const walk = (x - startX);
  const newLeft = startLeft + walk;
  const timelineWidth = document.querySelector('.timeline').offsetWidth;

  // Ensure the cursor stays within bounds
  if (newLeft >= 0 && newLeft <= timelineWidth) {
    cursor.style.left = `${newLeft}px`;

    // Update the value based on cursor position relative to the center
    const hoursFromNow = ((newLeft - (timelineWidth / 2)) / timelineWidth) * 48;
    cursor.setAttribute('value', hoursFromNow.toFixed(0));

    // Update the duration display and tooltip
    updateTimeline();
  }
};

const handleMouseUp = () => {
  isDragging = false;
  document.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('touchmove', handleMouseMove);
  document.removeEventListener('mouseup', handleMouseUp);
  document.removeEventListener('touchend', handleMouseUp);

  // Trigger station data update
  const duration = parseInt(cursor.getAttribute('value'), 10);
  const variable = document.getElementById('variable-select-dropdown').value;
  updateStationsData(duration, windImagesUrl, variable);
};

cursor.addEventListener('mousedown', handleMouseDown);
cursor.addEventListener('touchstart', handleMouseDown);
