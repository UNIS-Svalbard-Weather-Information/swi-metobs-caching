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
                    legendHtml += `<h3>${layerName}</h3>`;

                    // Add layer description if available
                    if (geojsonData.description) {
                        legendHtml += `<p>${geojsonData.description}</p>`;
                    }

                    legendHtml += `<div class="legend-dates">`;

                    if (geojsonData.date) {
                        legendHtml += `<p>
                            <strong>Published:</strong>
                            <span class="legend-date">
                                ${formatDate(geojsonData.date)}
                                <span class="info-icon" onclick="showPopup(event, 'The date when this data was first made available or published')">ℹ️</span>
                            </span>
                        </p>`;
                    }

                    if (geojsonData.lastDownload) {
                        legendHtml += `<p>
                            <strong>Updated:</strong>
                            <span class="legend-date">
                                ${formatDate(geojsonData.lastDownload, true)}
                                <span class="info-icon" onclick="showPopup(event, 'The last date and time when the data source was checked for updates')">ℹ️</span>
                            </span>
                        </p>`;
                    }

                    legendHtml += `</div><ul>`;

                    const uniqueStyles = new Set();

                    geojsonData.features.forEach(feature => {
                        const properties = feature.properties || {};
                        const color = properties.color || '#3388ff'; // Default color
                        const label = properties.name || 'Feature';
                        const fillOpacity = properties.fillOpacity || 0.9; // Default fill opacity
                        const description = properties.description; // Feature description

                        // Avoid duplicate entries in the legend
                        const uniqueKey = `${color}-${label}`;
                        if (!uniqueStyles.has(uniqueKey)) {
                            uniqueStyles.add(uniqueKey);
                            legendHtml += `
                                <li class="legend-item">
                                    <span class="geojson-legend-icon" style="background-color: ${color};"></span>
                                    <span class="legend-label">
                                        <strong>${label}</strong>`;
                            if (description) {
                                legendHtml += `<br><span class="feature-description">${description}</span>`;
                            }
                            legendHtml += `</span></li>`;
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




