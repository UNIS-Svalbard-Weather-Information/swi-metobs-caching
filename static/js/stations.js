let trackLayers = {};
let boatMarkers = {};
let windMarkers = {};
let mobileStations = {};

function loadStations(mobileStationConfigUrl, windImagesUrl) {
    fetch(mobileStationConfigUrl)
        .then(response => response.json())
        .then(stations => {
            mobileStations = stations;
            const projectControls = document.getElementById('project-controls');
            const projects = {};

            stations.forEach(station => {
                const project = station.project || 'Uncategorized';
                if (!projects[project]) {
                    projects[project] = [];
                }
                projects[project].push(station);
            });

            for (const project in projects) {
                const projectDiv = document.createElement('div');
                const projectLabel = document.createElement('label');
                projectLabel.textContent = project;
                projectDiv.appendChild(projectLabel);

                projects[project].forEach(station => {
                    const stationDiv = document.createElement('div');
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

            const durationSelect = document.getElementById('track-duration-select');
            const variableSelect = document.getElementById('variable-select-dropdown');
            
            durationSelect.addEventListener('change', () => {
                const duration = parseInt(durationSelect.value, 10);
                const variable = variableSelect.value;
                mobileStations.forEach(station => {
                    updateMobileStationData(station, duration, windImagesUrl, variable);
                });
            });

            variableSelect.addEventListener('change', () => {
                const duration = parseInt(durationSelect.value, 10);
                const variable = variableSelect.value;
                mobileStations.forEach(station => {
                    updateMobileStationData(station, duration, windImagesUrl, variable);
                });
            });

            // Initial load with default duration (1 hour) and variable (none)
            const initialDuration = parseInt(durationSelect.value, 10);
            const initialVariable = variableSelect.value;
            mobileStations.forEach(station => {
                updateMobileStationData(station, initialDuration, windImagesUrl, initialVariable);
            });
        })
        .catch(error => {
            console.error('Error loading stations:', error);
        });
}

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

function toggleStation(stationId, isVisible, windImagesUrl) {
    console.log(trackLayers[stationId])
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
    } else {
        const durationSelect = document.getElementById('track-duration-select');
        const variableSelect = document.getElementById('variable-select-dropdown');
        const duration = parseInt(durationSelect.value, 10);
        const variable = variableSelect.value;

        const station = mobileStations.find(s => s.id === stationId);
        updateMobileStationData(station, duration, windImagesUrl, variable);
    }
}

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
                    L.circleMarker(latlngs[i], {
                        radius: 5,
                        color: colorScale(values[i]),
                        fillColor: colorScale(values[i]),
                        fillOpacity: 0.9
                    })
                    .bindPopup(createPopupContent(station.name, data.track[i].variable))
                    .addTo(map);

                }

                // Add popup to the last point
                L.circleMarker(latlngs[latlngs.length - 1], {
                    radius: 5,
                    color: colorScale(values[latlngs.length - 1]),
                    fillColor: colorScale(values[latlngs.length - 1]),
                    fillOpacity: 0.9
                })
                .bindPopup(createPopupContent(station.name, data.track[latlngs.length - 1].variable))
                .addTo(map);

                trackLayers[station.id] = segments;
                updateColorBar(variable, extendedMinValue, extendedMaxValue);
            }
        });
}

function createPopupContent(stationName, dataPoint) {
    const date = new Date(dataPoint.time * 1000);
    const dateString = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    const windDirectionLetter = getWindDirectionLetter(dataPoint.windDirection);

    return `
        <strong>${stationName}</strong><br>
        ${dateString}<br>
        ----<br>
        Air Temperature: ${dataPoint.airTemperature !== null && dataPoint.airTemperature !== undefined ? dataPoint.airTemperature.toFixed(2) : 'N/A'} °C<br>
        Sea Surface Temperature: ${dataPoint.seaSurfaceTemperature !== null && dataPoint.seaSurfaceTemperature !== undefined ? dataPoint.seaSurfaceTemperature.toFixed(2) : 'N/A'} °C<br>
        Wind Speed: ${dataPoint.windSpeed !== null && dataPoint.windSpeed !== undefined ? dataPoint.windSpeed.toFixed(2) : 'N/A'} m/s<br>
        Wind Direction: ${dataPoint.windDirection !== null && dataPoint.windDirection !== undefined ? `${dataPoint.windDirection.toFixed(2)}° (${windDirectionLetter})` : 'N/A'}<br>
        Relative Humidity: ${dataPoint.relativeHumidity !== null && dataPoint.relativeHumidity !== undefined ? dataPoint.relativeHumidity.toFixed(2) : 'N/A'} %
    `;
}

function getWindDirectionLetter(degrees) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(degrees / 45) % 8;
    return directions[index];
}

function updateBoatMarker(station, data, variable) {
    //const boatIconUrl = '/static/images/boat_icon.png';
    const boatIcon = L.icon({
        iconUrl: station.icon,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    if (boatMarkers[station.id]) {
        map.removeLayer(boatMarkers[station.id]);
    }

    const variableInfo = createPopupContent(station.name, data.latest);
    const boatMarker = L.marker([data.lat, data.lon], { icon: boatIcon }).addTo(map);
    boatMarker.bindPopup(variableInfo);
    boatMarkers[station.id] = boatMarker;
}

function updateWindMarker(station, data, windImagesUrl) {
    const iconUrl = getWindSpeedIcon(windImagesUrl, data.windSpeed);
    //const windIcon = L.icon({
    //    iconUrl: iconUrl,
    //    iconSize: [48, 48], // Increase the size of the wind icon
    //    iconAnchor: [24, 24]
    //});

    var windRotatedIcon = L.divIcon({
        className: 'custom-icon',
        html: `<img src="${iconUrl}" class="rotated-icon" style="transform: rotate(${data.windDirection - 90}deg);" />`,
        iconSize: [50, 50], // size of the icon
        iconAnchor: [25, 25] // point of the icon which will correspond to marker's location
      });
  
      //L.marker([data.lat, data.lon], { icon: rotatedIcon }).addTo(map);

    if (windMarkers[station.id]) {
        map.removeLayer(windMarkers[station.id]);
    }

    const windMarker = L.marker([data.lat, data.lon], { 
        icon: windRotatedIcon,
    }).addTo(map);

    windMarker.bindPopup(createPopupContent(station.name, data.latest));
    windMarkers[station.id] = windMarker;
}

function getWindSpeedIcon(basePath, windSpeed) {
    const windSpeeds = [0, 5, 10, 15, 20, 25, 30, 35, 50, 55, 60, 65, 100, 105];
    let closest = windSpeeds.reduce((prev, curr) => Math.abs(curr - windSpeed) < Math.abs(prev - windSpeed) ? curr : prev);
    return `${basePath}/${closest.toString().padStart(2, '0')}kts.gif`;
}

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
