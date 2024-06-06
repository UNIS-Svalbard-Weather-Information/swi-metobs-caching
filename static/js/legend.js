function updateLegend(layer, legendControl) {
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
