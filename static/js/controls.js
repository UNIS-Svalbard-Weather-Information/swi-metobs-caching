/**
 * Adds an opacity control slider for a specific layer to the UI.
 * 
 * @param {string} layerName - The unique name of the layer.
 * @param {object} layerObj - The Leaflet layer object associated with the layer.
 */
function addOpacityControl(layerName, layerObj) {
    const opacityControls = document.getElementById('opacity-controls');

    // HTML for the opacity slider control
    const controlHtml = `
        <div class="opacity-control" id="opacity-${layerName}">
            <label>${layerName}</label><br>
            <input type="range" min="0" max="100" value="100" 
                   onchange="updateLayerOpacity('${layerName}', this.value)">
        </div>
    `;

    // Add the control to the opacity controls container
    opacityControls.insertAdjacentHTML('beforeend', controlHtml);
}

/**
 * Removes an opacity control slider for a specific layer from the UI.
 * 
 * @param {string} layerName - The unique name of the layer whose control should be removed.
 */
function removeOpacityControl(layerName) {
    const control = document.getElementById(`opacity-${layerName}`);

    // Remove the control if it exists
    if (control) {
        control.remove();
    }
}

/**
 * Updates the opacity of a given layer based on the value from the opacity slider.
 * 
 * @param {string} layerName - The unique name of the layer.
 * @param {number} value - The new opacity value (0 to 100) from the slider.
 */
function updateLayerOpacity(layerName, value) {
    const layer = additionalLayers[layerName];

    if (layer) {
        console.log(`Updating opacity for layer: ${layerName}, value: ${value}`);

        // Adjust opacity for layers that support the setOpacity method
        if (layer.setOpacity) {
            layer.setOpacity(value / 100);
        } 
        // Adjust opacity for GeoJSON or styled layers using setStyle
        else if (layer.setStyle) {
            layer.setStyle({
                opacity: value / 100,      // Line or contour opacity
                fillOpacity: value / 100  // Fill opacity for polygons
            });
        } 
        // Log a warning for unsupported layers
        else {
            console.warn(`Layer does not support opacity adjustment: ${layerName}`);
        }
    } 
    // Log an error if the layer is not found in additionalLayers
    else {
        console.error(`Layer not found in additionalLayers: ${layerName}`);
    }
}
