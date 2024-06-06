let additionalLayers = {};
let map;
let trackLayers = {};
let boatMarkers = {};
let windMarkers = {};
let colorBar;
let mobileStations = {};

function loadMap(layerConfigUrl, mobileStationConfigUrl, windImagesUrl) {
    fetch(layerConfigUrl)
        .then(response => response.json())
        .then(layerConfig => {
            map = L.map('map').setView([0, 0], 2);
            const baseLayers = {};
            additionalLayers = {};
            trackLayers = {};
            boatMarkers = {};
            windMarkers = {};
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
                });
        });
}

function fetchMobileStationData(station, duration, variable) {
    return fetch(`/api/mobile-station-data/${station.id}?duration=${duration}&variable=${variable}`)
        .then(response => response.json());
}

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
        fetchMobileStationData(station, duration, variable)
            .then(data => {
                updateBoatMarker(station.id, data, variable);
                updateWindMarker(station.id, data, windImagesUrl);
            });
        return;
    }

    fetchMobileStationData(station, duration, variable)
        .then(data => {
            updateBoatMarker(station.id, data, variable);
            updateWindMarker(station.id, data, windImagesUrl);

            const latlngs = data.track.map(dp => [dp.lat, dp.lon]);
            const values = data.track.map(dp => dp.variable);
            const minValue = Math.min(...values);
            const maxValue = Math.max(...values);
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
            }

            trackLayers[station.id] = segments;
            updateColorBar(variable, extendedMinValue, extendedMaxValue);
        });
}

function updateBoatMarker(stationId, data, variable) {
    const boatIconUrl = '/static/images/boat_icon.png';
    const boatIcon = L.icon({
        iconUrl: boatIconUrl,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    if (boatMarkers[stationId]) {
        map.removeLayer(boatMarkers[stationId]);
    }

    const variableInfo = variable !== 'none' && data.variable !== null ? `<br>${variable}: ${data.variable}` : '';
    const boatMarker = L.marker([data.lat, data.lon], { icon: boatIcon }).addTo(map);
    boatMarker.bindPopup(`Boat: ${stationId}<br>Wind Speed: ${data.windSpeed} kts<br>Wind Direction: ${data.windDirection}°${variableInfo}`);
    boatMarkers[stationId] = boatMarker;
}

function updateWindMarker(stationId, data, windImagesUrl) {
    const iconUrl = getWindSpeedIcon(windImagesUrl, data.windSpeed);
    const windIcon = L.icon({
        iconUrl: iconUrl,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    if (windMarkers[stationId]) {
        map.removeLayer(windMarkers[stationId]);
    }

    const windMarker = L.marker([data.lat, data.lon], { icon: windIcon }).addTo(map);
    windMarker.bindPopup(`Wind Speed: ${data.windSpeed} kts<br>Wind Direction: ${data.windDirection}°`);
    windMarkers[stationId] = windMarker;
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

function updateColorBar(variable, minValue, maxValue) {
    if (colorBar) {
        map.removeControl(colorBar);
    }

    if (variable === 'none') {
        return;
    }

    const colorBarDiv = L.DomUtil.create('div', 'info legend');
    const colorScale = getColorScale(variable, minValue, maxValue);

    const legend = d3.select(colorBarDiv)
        .append('svg')
        .attr('width', 100)
        .attr('height', 300);

    const gradient = legend.append('defs')
        .append('linearGradient')
        .attr('id', 'gradient')
        .attr('x1', '0%')
        .attr('x2', '0%')
        .attr('y1', '0%')
        .attr('y2', '100%');

    const stops = d3.range(0, 1.01, 0.01).map(t => ({
        offset: `${t * 100}%`,
        color: colorScale(minValue + t * (maxValue - minValue))
    }));

    gradient.selectAll('stop')
        .data(stops)
        .enter()
        .append('stop')
        .attr('offset', d => d.offset)
        .attr('stop-color', d => d.color);

    legend.append('rect')
        .attr('width', 20)
        .attr('height', 300)
        .style('fill', 'url(#gradient)');

    const axisScale = d3.scaleLinear()
        .domain([minValue, maxValue])
        .range([300, 0]);

    const axis = d3.axisRight(axisScale)
        .ticks(5);

    legend.append('g')
        .attr('class', 'axis')
        .attr('transform', 'translate(20, 0)')
        .call(axis);

    colorBar = L.control({ position: 'bottomright' });
    colorBar.onAdd = function () {
        return colorBarDiv;
    };
    colorBar.addTo(map);
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
