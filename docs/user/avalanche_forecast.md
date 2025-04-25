# Avalanche Forecast Integration

The SWI includes the capability to display avalanche forecasts as a geographic layer, which can be overlaid on the map. These layers are generated using avalanche forecast data retrieved from the NVE API, the same data source used by Varsom.no.

From the forecast data, we create a feature that highlights all slopes between 25° and 65°, as identified in the forecast. This range is critical because it represents the angles where avalanches are most likely to initiate (McCammon & Schweizer, 2009). We select slopes based on their orientation and elevation as specified in the forecast.

To generate the layer that represents the shape of the given area, we utilize the Digital Elevation Model (DEM) of Svalbard provided by the Norwegian Polar Institute (Norwegian Polar Institute, 2014). This DEM is processed to create an aspect raster, a steepness raster, and finally, the contour shapefile of the selected area.

**Prevention and Safety:**

Understanding the avalanche danger scale is crucial for safety in avalanche-prone areas. The scale ranges from Low to Extreme and provides essential information about the likelihood and potential size of avalanches. For more detailed information on the avalanche danger scale and safety measures, please refer to [Avalanche Danger Scale](https://www.avalanches.org/education/avalanche-danger-scale-2/).

Additionally, it is important to be aware that avalanches can be remotely triggered, and the runout area can extend far beyond the initial avalanche zone. For comprehensive information on avalanche prevention and safety, visit [Varsom's Avalanche Information](https://www.varsom.no/en/avalanches/about-avalanches/).

**References:**

- McCammon, I., & Schweizer, J. (2009). [Snow and avalanche research](https://gblanc.fr/IMG/pdf/mccammon2009.pdf).
- Norwegian Polar Institute. (2014). *Terrengmodell Svalbard (S0 Terrengmodell)*. Norwegian Polar Institute. [https://data.npolar.no/dataset/dce53a47-c726-4845-85c3-a65b46fe2fea](https://data.npolar.no/dataset/dce53a47-c726-4845-85c3-a65b46fe2fea)