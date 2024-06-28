const variableUnits = {
    "airTemperature": "Temperature [°C]",
    "seaSurfaceTemperature": "Sea Surface Temp [°C]",
    "windSpeed": "Wind Speed [m/s]",
    "windDirection": "Wind Direction [°]",
    "relativeHumidity": "Relative Humidity [%]"
};



function updateLegend(legendControl) {
    let legendHtml = '<h4>Legend</h4>';

    if (Object.keys(activeLayers).length === 0) {
        legendControl._div.innerHTML = legendHtml;
        return;
    }

    let legendPromises = [];

    for (let layerName in activeLayers) {
        const layer = activeLayers[layerName];
        if (layer.type === 'wms') {
            const legendUrl = `${layer.url}?SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=${layer.layers}`;
            legendHtml += `<img src="${legendUrl}" alt="Legend">`;
        } else if (layer.type === 'arcgis') {
            legendPromises.push(
                fetch(`${layer.url}/legend?f=pjson`)
                    .then(response => response.json())
                    .then(data => {
                        legendHtml += `<strong>${layerName}</strong><br><ul>`;
                        data.layers.forEach(layerItem => {
                            if (layer.layers.includes(layerItem.layerId)) {
                                legendHtml += `<li><strong>${layerItem.layerName}</strong><br>`;
                                layerItem.legend.forEach(item => {
                                    legendHtml += `<img src="data:image/png;base64,${item.imageData}" alt="${item.label}"> ${item.label}<br>`;
                                });
                                legendHtml += '</li>';
                            }
                        });
                        legendHtml += '</ul>';
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



