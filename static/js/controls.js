function addOpacityControl(layerName, layerObj) {
    const opacityControls = document.getElementById('opacity-controls');
    const controlHtml = `
        <div class="opacity-control" id="opacity-${layerName}">
            <label>${layerName}</label><br>
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
        console.log(`Updating opacity for layer: ${layerName}, value: ${value}`);
        if (layer.setOpacity) {
            // For layers with setOpacity method (e.g., tile layers, WMS layers)
            layer.setOpacity(value / 100);
        } else if (layer.setStyle) {
            // For GeoJSON layers or other styled layers
            layer.setStyle({
                opacity: value / 100,      // Applies to contours (e.g., lines)
                fillOpacity: value / 100  // Applies to fills (e.g., polygons)
            });
        } else {
            console.warn(`Layer does not support opacity adjustment: ${layerName}`);
        }
    } else {
        console.error(`Layer not found in additionalLayers: ${layerName}`);
    }
}