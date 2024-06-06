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
