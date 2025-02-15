const variableUnits = {
    "airTemperature": "Temperature [°C]",
    "seaSurfaceTemperature": "Sea Surface Temp [°C]",
    "windSpeed": "Wind Speed [m/s]",
    "windDirection": "Wind Direction [°]",
    "relativeHumidity": "Relative Humidity [%]"
};

/**
 * Formats an ISO date string to a specified format.
 * @param {string} isoDate - The ISO date string (e.g., "2024-11-16T14:30:00Z").
 * @param {boolean} includeTime - Whether to include time in the output (default: false).
 * @returns {string} - The formatted date string.
 */
function formatDate(isoDate, includeTime = false) {
    if (!isoDate) return 'N/A';

    const date = new Date(isoDate);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    let formattedDate = `${day}.${month}.${year}`;
    if (includeTime) {
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        formattedDate += ` ${hours}:${minutes}`;
    }
    return formattedDate;
}


function updateLegend(legendControl) {
    // Add the legend-container class to the div
    legendControl._div.classList.add('legend-container');

    // Prevent map scroll when interacting with the legend
    legendControl._div.addEventListener('wheel', function (e) {
        e.stopPropagation();
    });

    let legendHtml = '<h2>Legend</h2>';

    if (Object.keys(activeLayers).length === 0) {
        legendControl._div.innerHTML = legendHtml;
        return;
    }

    let legendPromises = [];

    for (let layerName in activeLayers) {
        const layer = activeLayers[layerName];

        if (layer.type === 'geojson') {
            // Fetch the GeoJSON data for the layer
            legendPromises.push(
                fetch(layer.url)
                    .then(response => {
                        if (!response.ok) throw new Error(`Failed to fetch GeoJSON for ${layerName}`);
                        return response.json();
                    })
                    .then(geojsonData => {
                        legendHtml += `<h3>${layerName}</h3><ul>`;



                        legendHtml += `
                            <div class="legend-dates">
                                ${
                                    geojsonData.date
                                        ? `<p>
                                            <strong>Published:</strong> 
                                            <span 
                                                class="legend-date">
                                                ${formatDate(geojsonData.date)}
                                                <span 
                                                    class="info-icon" 
                                                    onclick="showPopup(event, 'The date when this data was first made available or published')">
                                                    ℹ️
                                                </span>
                                            </span>
                                        </p>`
                                        : ''
                                }
                                ${
                                    geojsonData.lastDownload
                                        ? `<p>
                                            <strong>Updated:</strong> 
                                            <span 
                                                class="legend-date">
                                                ${formatDate(geojsonData.lastDownload, true)}
                                                <span 
                                                    class="info-icon" 
                                                    onclick="showPopup(event, 'The last date and time when the data source was checked for updates')">
                                                    ℹ️
                                                </span>
                                            </span>
                                        </p>`
                                        : ''
                                }
                            </div>
                        `;
                        const uniqueStyles = new Set();

                        geojsonData.features.forEach(feature => {
                            const properties = feature.properties || {};
                            const color = properties.color || '#3388ff'; // Default color
                            const label = properties.name || 'Feature';

                            // Avoid duplicate entries in the legend
                            const uniqueKey = `${color}-${label}`;
                            if (!uniqueStyles.has(uniqueKey)) {
                                uniqueStyles.add(uniqueKey);
                                legendHtml += `
                                    <li class="legend-item">
                                        <span class="geojson-legend-icon" style="background-color: ${color};"></span>
                                        <span>${label}</span>
                                    </li>`;
                            }
                        });

                        legendHtml += '</ul>';
                    })
                    .catch(error => {
                        console.error(error);
                        legendHtml += `<div class="legend-error">Error loading legend for ${layerName}</div>`;
                    })
            );
        } else if (layer.type === 'wms') {
            const legendUrl = `${layer.url}?SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=${layer.layers}`;
            legendHtml += `<div class="legend-item"><img src="${legendUrl}" alt="Legend"> <span>${layerName}</span></div>`;
        } else if (layer.type === 'arcgis') {
            legendPromises.push(
                fetch(`${layer.url}/legend?f=pjson`)
                    .then(response => {
                        if (!response.ok) throw new Error(`Failed to fetch legend for ${layerName}`);
                        return response.json();
                    })
                    .then(data => {
                        legendHtml += `<h3>${layerName}</h3><ul>`;
                        data.layers.forEach(layerItem => {
                            if (layer.layers.includes(layerItem.layerId)) {
                                legendHtml += `<li><strong>${layerItem.layerName}</strong><ul>`;
                                layerItem.legend.forEach(item => {
                                    legendHtml += `
                                        <li class="legend-item">
                                            <img src="data:image/png;base64,${item.imageData}" alt="${item.label}">
                                            <span>${item.label}</span>
                                        </li>`;
                                });
                                legendHtml += '</ul></li>';
                            }
                        });
                        legendHtml += '</ul>';
                    })
                    .catch(error => {
                        console.error(error);
                        legendHtml += `<div class="legend-error">Error loading legend for ${layerName}</div>`;
                    })
            );
        }
    }

    Promise.all(legendPromises).then(() => {
        legendControl._div.innerHTML = legendHtml;
    });
}

function updateColorBar(variable, minValue, maxValue, colorScale) {
    // Remove the existing color bar if it exists
    d3.select('.colorBar').remove();

    if (variable === 'none') {
        return;
    }
  
    // Create a new legend control
    var legend = L.control({position: 'bottomleft'});
  
    legend.onAdd = function (map) {
      var div = L.DomUtil.create('div', 'colorBar');
      var width = 300;
      var height = 60; // Increase height to accommodate variable name and unit
      var svg = d3.select(div).append('svg')
        .attr('width', width)
        .attr('height', height);
  
      var gradient = svg.append('defs')
        .append('linearGradient')
        .attr('id', 'gradient')
        .attr('x1', '0%')
        .attr('x2', '100%')
        .attr('y1', '0%')
        .attr('y2', '0%');
  
      // Define the gradient stops based on the color scale
      gradient.selectAll('stop')
        .data(d3.range(minValue, maxValue, (maxValue - minValue) / 10))
        .enter().append('stop')
        .attr('offset', d => ((d - minValue) / (maxValue - minValue)) * 100 + '%')
        .attr('stop-color', d => colorScale(d));
  
      // Draw the rectangle and fill with gradient
      svg.append('rect')
        .attr('width', width)
        .attr('height', 20)
        .attr('y', 20)
        .style('fill', 'url(#gradient)');
  
      // Add labels
      var xScale = d3.scaleLinear()
        .domain([minValue, maxValue])
        .range([0, width]);
  
      var xAxis = d3.axisBottom(xScale)
        .ticks(5);
  
      svg.append('g')
        .attr('class', 'axis')
        .attr('transform', 'translate(0,40)')
        .call(xAxis);
  
      // Add variable name and unit
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', 15)
        .attr('text-anchor', 'middle')
        .style('font-size', '14px')
        .style('font-weight', 'bold')
        .text(variableUnits[variable] || variable);
  
      return div;
    };
  
    // Add the new legend to the map
    legend.addTo(map);
  }

function updateColorBar2(variable, minValue, maxValue, colorScale) {
    if (colorBar) {
        map.removeControl(colorBar);
    }

    if (variable === 'none') {
        return;
    }

    // Mapping of variables to their units
    const variableUnits = {
        "airTemperature": "Temperature [°C]",
        "seaSurfaceTemperature": "Sea Surface Temp [°C]",
        "windSpeed": "Wind Speed [m/s]",
        "windDirection": "Wind Direction [°]",
        "relativeHumidity": "Relative Humidity [%]"
    };

    const colorBarDiv = L.DomUtil.create('div', 'info legend');
    //const colorScale = getColorScale(variable, minValue, maxValue);

    const legend = d3.select(colorBarDiv)
        .append('svg')
        .attr('width', 100)  // Increased width to accommodate rotated label
        .attr('height', 350); // Increased height for the label

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
        .attr('x', 10)  // Shifted to the right to make space for the label
        .attr('width', 20)
        .attr('height', 300)
        .style('fill', 'url(#gradient)');

    const axisScale = d3.scaleLinear()
        .domain([minValue, maxValue])
        .range([300, 0]);

    const axis = d3.axisRight(axisScale)
        .ticks(5);

    const axisGroup = legend.append('g')
        .attr('class', 'axis')
        .attr('transform', 'translate(30, 0)')  // Adjusted to align with the color bar
        .call(axis);

    // Increase the font size for the axis
    axisGroup.selectAll('text')
        .style('font-size', '14px');

    // Adding rotated label for variable and unit
    legend.append('text')
        .attr('x', 60)  // Position to the right of the axis
        .attr('y', 150)  // Middle of the color bar
        .attr('transform', 'rotate(-90, 60, 150)')  // Rotate 90 degrees around the label position
        .attr('dy', '.35em')
        .attr('text-anchor', 'middle')
        .style('font-size', '16px')  // Increase the font size for the label
        .text(variableUnits[variable] || variable);

    colorBar = L.control({ position: 'bottomleft' });
    colorBar.onAdd = function () {
        return colorBarDiv;
    };
    colorBar.addTo(map);
}

function showPopup(event, message) {
    // Check if a popup already exists
    let existingPopup = document.querySelector('.popup-box');
    if (existingPopup) existingPopup.remove(); // Remove existing popup if any

    // Create a new popup
    const popup = document.createElement('div');
    popup.className = 'popup-box';
    popup.textContent = message;

    // Append the popup to the body
    document.body.appendChild(popup);

    // Find the legend container and calculate its position
    const legend = document.querySelector('.info.legend');
    const legendRect = legend.getBoundingClientRect();
    const popupWidth = popup.offsetWidth;
    const popupHeight = popup.offsetHeight;

    // Default positioning near the legend
    let left = legendRect.left + legendRect.width / 2 - popupWidth / 2; // Centered horizontally to the legend
    let top = legendRect.top + legendRect.height + 10; // 10px below the legend

    // Ensure the popup stays within the viewport
    if (left < 0) left = 10; // Align to the left edge of the screen with padding
    if (left + popupWidth > window.innerWidth) left = window.innerWidth - popupWidth - 10; // Align to the right edge
    if (top + popupHeight > window.innerHeight) top = legendRect.top - popupHeight - 10; // Move above the legend if it overflows

    // Apply calculated positioning
    popup.style.left = `${left}px`;
    popup.style.top = `${top}px`;

    // Automatically hide the popup after a few seconds
    setTimeout(() => popup.remove(), 4000);

    // Close the popup on clicking anywhere else
    document.addEventListener(
        'click',
        (e) => {
            if (!popup.contains(e.target) && e.target !== event.target) {
                popup.remove();
            }
        },
        { once: true }
    );
}




