import os
import zipfile
import requests
import tempfile
import shutil
import rasterio
from rasterio.features import shapes
import numpy as np
import geopandas as gpd
from shapely.geometry import shape, Polygon
from source.logger.logger import Logger

ORIENTATION_RANGES = {
    'N': [(315, 360), (0, 45)],
    'NE': [(45, 90)],
    'E': [(90, 135)],
    'SE': [(135, 180)],
    'S': [(180, 225)],
    'SW': [(225, 270)],
    'W': [(270, 315)],
    'NW': [(315, 360)]
}

class MapsCaching:
    """
    A class to manage the downloading and processing of Digital Elevation Models (DEMs),
    computing steepness rasters, and creating steepness contours.

    Attributes:
        path (str): The base path where files will be stored.
        force (bool): If True, forces the recreation of layers even if they already exist.
        DEM_res (dict): A dictionary mapping DEM resolutions to their download URLs.
        logger (Logger): A logger instance for logging messages.
        DEM_path (str): The file path to the downloaded DEM.
        steepness_raster_path (str): The file path to the computed steepness raster.
        contour_path (str): The file path to the created steepness contour shapefile.
    """

    def __init__(self, path='./static/maps/', force=False):
        """
        Initializes the MapsCaching instance and ensures the managed directory exists.

        Args:
            path (str): The base path where files will be stored.
            force (bool): If True, forces the recreation of layers even if they already exist.
        """
        self.path = path
        self.force = force
        self.DEM_res = {
            'DTM50': 'https://next.api.npolar.no/dataset/dce53a47-c726-4845-85c3-a65b46fe2fea/attachment/838be1e3-58ef-4338-b80c-dec86ba07bd2/_blob',
            'DTM20': 'https://next.api.npolar.no/dataset/dce53a47-c726-4845-85c3-a65b46fe2fea/attachment/e3c4ca92-fde2-4abc-87e8-6a2d4a14863a/_blob'
        }
        self.logger = Logger.setup_logger('MapsCaching')

        # Ensure the managed directory exists
        managed_path = os.path.join(self.path, 'managed')
        os.makedirs(managed_path, exist_ok=True)

        self.DEM_path = self._find_existing_DEM()
        self.steepness_raster_path = self._find_existing_steepness_raster()
        self.contour_path = self._find_existing_contour()

        if self.force:
            self.DEM_path = None
            self.steepness_raster_path = None
            self.contour_path = None

    def _find_existing_DEM(self):
        """
        Finds an existing DEM file in the managed directory.

        Returns:
            str: The file path to the existing DEM, or None if not found.
        """
        managed_path = os.path.join(self.path, 'managed')
        for res in self.DEM_res.keys():
            dem_filename = f"{res}_DEM_*.tif"
            for file in os.listdir(managed_path):
                if file.startswith(f"{res}_DEM_") and file.endswith('.tif'):
                    return os.path.join(managed_path, file)
        return None

    def _find_existing_steepness_raster(self):
        """
        Finds an existing steepness raster file in the managed directory.

        Returns:
            str: The file path to the existing steepness raster, or None if not found.
        """
        managed_path = os.path.join(self.path, 'managed')
        for res in self.DEM_res.keys():
            steepness_filename = f'{res}_steepness_raster.tif'
            steepness_path = os.path.join(managed_path, steepness_filename)
            if os.path.exists(steepness_path):
                return steepness_path
        return None

    def _find_existing_contour(self):
        """
        Finds an existing contour file in the managed directory.

        Returns:
            str: The file path to the existing contour, or None if not found.
        """
        managed_path = os.path.join(self.path, 'managed')
        for file in os.listdir(managed_path):
            if file.startswith('steepness_contour_') and file.endswith('.shp'):
                return os.path.join(managed_path, file)
        return None

    def _download_DEM(self, res='DTM50'):
        """
        Downloads the DEM file from the specified URL and extracts it.

        Args:
            res (str): The resolution of the DEM to download.
        """
        url = self.DEM_res.get(res)
        if not url:
            self.logger.error(f"Resolution {res} not found.")
            return

        self.logger.info(f"Downloading DEM with resolution {res} from {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()

            # Use a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, 'temp.zip')

                with open(zip_path, 'wb') as file:
                    file.write(response.content)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith('.tif') or file.endswith('.txt'):
                                old_file_path = os.path.join(root, file)
                                new_name = os.path.join(self.path, 'managed', f"{res}_DEM_{file}")
                                shutil.move(old_file_path, new_name)
                                if new_name.endswith('.tif'):
                                    self.DEM_path = new_name
                                self.logger.info(f"DEM file moved and renamed to {new_name}")

            self.logger.info(f"DEM downloaded and extracted to {os.path.join(self.path, 'managed')}")

        except requests.RequestException as e:
            self.logger.error(f"Failed to download DEM: {e}")
        except zipfile.BadZipFile as e:
            self.logger.error(f"Failed to extract DEM: {e}")

    def _compute_steepness_raster(self, res='DTM50'):
        """
        Computes the steepness raster from the DEM file.

        Args:
            res (str): The resolution of the DEM to use.
        """
        # Ensure DEM is downloaded
        self.get_DEM(res)

        if not self.DEM_path:
            self.logger.error("DEM not available. Please download DEM first.")
            return

        self.logger.info(f"Computing steepness raster from {self.DEM_path}")

        try:
            with rasterio.open(self.DEM_path) as src:
                elevation = src.read(1)
                profile = src.profile

                x_res = profile['transform'][0]
                y_res = -profile['transform'][4]

                # Compute gradient in x and y direction
                gradient_x, gradient_y = np.gradient(elevation, x_res, y_res)
                slope = np.arctan(np.sqrt(gradient_x**2 + gradient_y**2)) * (180 / np.pi)

                # Save the slope raster
                steepness_path = os.path.join(self.path, 'managed', f'{res}_steepness_raster.tif')
                with rasterio.open(
                    steepness_path,
                    'w',
                    driver='GTiff',
                    height=slope.shape[0],
                    width=slope.shape[1],
                    count=1,
                    dtype=slope.dtype,
                    crs=src.crs,
                    transform=src.transform
                ) as dst:
                    dst.write(slope, 1)

                self.steepness_raster_path = steepness_path
                self.logger.info(f"Steepness raster computed and saved to {steepness_path}")

        except Exception as e:
            self.logger.error(f"Failed to compute steepness raster: {e}")

    def _create_steepness_contour(self, min_steepness, max_steepness, res='DTM50', orientation=None):
        """
        Creates a shapefile with smoothed polygons representing areas within a specified steepness range,
        optionally filtered by orientation.

        Args:
            min_steepness (float): The minimum steepness value for the contour.
            max_steepness (float): The maximum steepness value for the contour.
            res (str): The resolution of the DEM to use.
            orientation (str): The orientation to filter the contour by (e.g., 'N', 'NE', 'E', etc.).

        Returns:
            str: The file path to the created contour shapefile.
        """
        # Ensure steepness raster is computed
        self.get_steepness_raster(res)
        aspect_path = self.get_aspect_raster(res)

        if not self.steepness_raster_path:
            self.logger.error("Steepness raster not available.")
            return None

        if orientation and not aspect_path:
            self.logger.error("Aspect raster not available.")
            return None

        self.logger.info(f"Creating steepness contour for range {min_steepness}-{max_steepness} degrees")

        try:
            # Set tolerance based on resolution
            tolerance = np.sqrt((50 if res == 'DTM50' else 20) ** 2 * 2)

            with rasterio.open(self.steepness_raster_path) as src_steepness:
                steepness = src_steepness.read(1)
                mask = (steepness >= min_steepness) & (steepness <= max_steepness)

                if orientation:
                    with rasterio.open(aspect_path) as src_aspect:
                        aspect = src_aspect.read(1)
                        orientation_mask = np.zeros_like(aspect, dtype=bool)
                        for min_aspect, max_aspect in ORIENTATION_RANGES[orientation]:
                            orientation_mask |= (aspect >= min_aspect) & (aspect < max_aspect)
                        mask = mask & orientation_mask

                shapes_gen = shapes(mask.astype(np.uint8), mask=mask, transform=src_steepness.transform)

                # Create a GeoDataFrame from the shapes
                polygons = [shape(geom) for geom, value in shapes_gen if value == 1]

                # Debugging output
                self.logger.info(f"Generated {len(polygons)} polygons for orientation {orientation}")
                feature_type = []
                for i, poly in enumerate(polygons):
                    feature_type.append(poly.geom_type)

                self.logger.info(f"Types are: {np.unique(feature_type)}")

                # Simplify polygons
                polygons = [poly.simplify(tolerance) for poly in polygons]

                gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=src_steepness.crs)

                # Save to shapefile
                contour_path = os.path.join(self.path, 'managed',
                                            f'{res}_steepness_contour_{min_steepness}_{max_steepness}_{orientation if orientation else ""}.shp')
                gdf.to_file(contour_path, driver='ESRI Shapefile')

                self.logger.info(f"Steepness contour shapefile created at {contour_path}")
                return contour_path

        except Exception as e:
            self.logger.error(f"Failed to create steepness contour: {e}")
            return None

    def _compute_aspect_raster(self, res='DTM50'):
        """
        Computes the aspect raster from the DEM file.

        Args:
            res (str): The resolution of the DEM to use.
        """
        # Ensure DEM is downloaded
        self.get_DEM(res)

        if not self.DEM_path:
            self.logger.error("DEM not available. Please download DEM first.")
            return

        self.logger.info(f"Computing aspect raster from {self.DEM_path}")

        try:
            with rasterio.open(self.DEM_path) as src:
                elevation = src.read(1)
                profile = src.profile

                x_res = profile['transform'][0]
                y_res = -profile['transform'][4]

                # Compute gradient in x and y direction
                gradient_x, gradient_y = np.gradient(elevation, x_res, y_res)
                aspect = np.arctan2(-gradient_y, gradient_x)

                # Convert radians to degrees and use modulo to ensure range [0, 360)
                aspect = np.rad2deg(aspect) % 360

                # Save the aspect raster
                aspect_path = os.path.join(self.path, 'managed', f'{res}_aspect_raster.tif')
                with rasterio.open(
                        aspect_path,
                        'w',
                        driver='GTiff',
                        height=aspect.shape[0],
                        width=aspect.shape[1],
                        count=1,
                        dtype=aspect.dtype,
                        crs=src.crs,
                        transform=src.transform
                ) as dst:
                    dst.write(aspect, 1)

                self.logger.info(f"Aspect raster computed and saved to {aspect_path}")
                return aspect_path

        except Exception as e:
            self.logger.error(f"Failed to compute aspect raster: {e}")
            return None

    def get_DEM(self, res='DTM50'):
        """
        Gets the file path to the DEM, downloading it if necessary.

        Args:
            res (str): The resolution of the DEM to use.

        Returns:
            str: The file path to the DEM.
        """
        if self.force or not self.DEM_path:
            self._download_DEM(res)
        if not self.DEM_path:
            self.logger.error("DEM download failed.")
            return None
        return self.DEM_path

    def get_steepness_raster(self, res='DTM50'):
        """
        Gets the file path to the steepness raster, computing it if necessary.

        Args:
            res (str): The resolution of the DEM to use.

        Returns:
            str: The file path to the steepness raster.
        """
        if self.force or not self.steepness_raster_path:
            self._compute_steepness_raster(res)
        if not self.steepness_raster_path:
            self.logger.error("Steepness raster computation failed.")
            return None
        return self.steepness_raster_path

    def get_steepness_contour(self, min_steepness, max_steepness, res='DTM50'):
        """
        Gets the file path to the steepness contour shapefile, creating it if necessary.

        Args:
            min_steepness (float): The minimum steepness value for the contour.
            max_steepness (float): The maximum steepness value for the contour.
            res (str): The resolution of the DEM to use.

        Returns:
            str: The file path to the steepness contour shapefile.
        """
        contour_filename = f'steepness_contour_{min_steepness}_{max_steepness}.shp'
        contour_path = os.path.join(self.path, 'managed', contour_filename)

        if self.force or not os.path.exists(contour_path):
            self.contour_path = self._create_steepness_contour(min_steepness, max_steepness, res)
        else:
            self.logger.info(f"Steepness contour already exists at {contour_path}")
            self.contour_path = contour_path

        return self.contour_path

    def get_aspect_raster(self, res='DTM50'):
        """
        Gets the file path to the aspect raster, computing it if necessary.

        Args:
            res (str): The resolution of the DEM to use.

        Returns:
            str: The file path to the aspect raster.
        """
        aspect_filename = f'{res}_aspect_raster.tif'
        aspect_path = os.path.join(self.path, 'managed', aspect_filename)

        if self.force or not os.path.exists(aspect_path):
            aspect_path = self._compute_aspect_raster(res)
        else:
            self.logger.info(f"Aspect raster already exists at {aspect_path}")

        return aspect_path

    def get_steepness_contour_direction(self, orientation, min_steepness=25, max_steepness=55, res='DTM50'):
        """
        Gets the file path to the steepness contour shapefile, creating it if necessary,
        optionally filtered by orientation.

        Args:
            min_steepness (float): The minimum steepness value for the contour.
            max_steepness (float): The maximum steepness value for the contour.
            res (str): The resolution of the DEM to use.
            orientation (str): The orientation to filter the contour by (e.g., 'N', 'NE', 'E', etc.).

        Returns:
            str: The file path to the steepness contour shapefile.
        """
        contour_filename = f'steepness_contour_{min_steepness}_{max_steepness}_{orientation if orientation else ""}.shp'
        contour_path = os.path.join(self.path, 'managed', contour_filename)

        if self.force or not os.path.exists(contour_path):
            self.contour_path = self._create_steepness_contour(min_steepness, max_steepness, res, orientation)
        else:
            self.logger.info(f"Steepness contour already exists at {contour_path}")
            self.contour_path = contour_path

        return self.contour_path
