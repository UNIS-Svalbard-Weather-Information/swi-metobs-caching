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
from tqdm import tqdm

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
    """

    def __init__(self, path='./static/maps/', force=False):
        """
        Initializes the MapsCaching instance and ensures the managed directory exists.

        Args:
            path (str): The base directory path for storing maps and related files.
            force (bool): Flag to force re-download and re-computation of files.
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
            str: Path to the existing DEM file, or None if not found.
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
            str: Path to the existing steepness raster file, or None if not found.
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
            str: Path to the existing contour file, or None if not found.
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

        self.logger.info(f"Starting download of DEM with resolution {res} from {url}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 Kibibyte

            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, 'temp.zip')

                with open(zip_path, 'wb') as file, tqdm(
                    desc=f"Downloading {res} DEM",
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        bar.update(len(data))

                self.logger.info("Download complete. Extracting files...")

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
        self.get_DEM(res)

        if not self.DEM_path:
            self.logger.error("DEM not available. Please download DEM first.")
            return

        self.logger.info(f"Starting computation of steepness raster from {self.DEM_path}")

        try:
            with rasterio.open(self.DEM_path) as src:
                elevation = src.read(1)
                profile = src.profile

                x_res = profile['transform'][0]
                y_res = -profile['transform'][4]

                self.logger.info("Calculating gradients...")
                gradient_x, gradient_y = np.gradient(elevation, x_res, y_res)
                slope = np.arctan(np.sqrt(gradient_x**2 + gradient_y**2)) * (180 / np.pi)

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

    def _create_steepness_contour(self, min_steepness, max_steepness, res='DTM50', orientations=None,
                                  elevation_start=None, elevation_end=None):
        """
        Creates a shapefile with smoothed polygons representing areas within a specified steepness range,
        optionally filtered by orientation and elevation range.

        Args:
            min_steepness (float): The minimum steepness value.
            max_steepness (float): The maximum steepness value.
            res (str): The resolution of the DEM to use.
            orientations (str, optional): The orientation to filter the contours by.
            elevation_start (float, optional): The minimum elevation value.
            elevation_end (float, optional): The maximum elevation value.

        Returns:
            str: Path to the created contour file, or None if creation failed.
        """
        self.get_steepness_raster(res)
        aspect_path = self.get_aspect_raster(res)

        if not self.steepness_raster_path:
            self.logger.error("Steepness raster not available.")
            return None

        if orientations and not aspect_path:
            self.logger.error("Aspect raster not available.")
            return None

        self.logger.info(
            f"Starting creation of steepness contour for range {min_steepness}-{max_steepness} degrees with orientation {orientations if orientations else 'all'} "
            f"and elevation range {elevation_start}-{elevation_end} meters."
        )

        try:
            tolerance = np.sqrt((50 if res == 'DTM50' else 20) ** 2 * 2)

            with rasterio.open(self.steepness_raster_path) as src_steepness:
                steepness = src_steepness.read(1)
                mask = (steepness >= min_steepness) & (steepness <= max_steepness)

                if orientations:
                    with rasterio.open(aspect_path) as src_aspect:
                        aspect = src_aspect.read(1)
                        orientation_mask = np.zeros_like(aspect, dtype=bool)
                        for orientation in orientations:
                            for min_aspect, max_aspect in ORIENTATION_RANGES[orientation]:
                                orientation_mask |= (aspect >= min_aspect) & (aspect < max_aspect)
                        mask = mask & orientation_mask

                if elevation_start is not None or elevation_end is not None:
                    with rasterio.open(self.DEM_path) as src_dem:
                        elevation = src_dem.read(1)
                        if elevation_start is not None:
                            mask = mask & (elevation >= elevation_start)
                        if elevation_end is not None:
                            mask = mask & (elevation <= elevation_end)

                shapes_gen = shapes(mask.astype(np.uint8), mask=mask, transform=src_steepness.transform)
                polygons = [shape(geom) for geom, value in tqdm(shapes_gen, desc="Generating polygons", unit="polygon")
                            if value == 1]

                self.logger.info(f"Generated {len(polygons)} polygons for orientation {orientations}")
                feature_type = [poly.geom_type for poly in polygons]
                self.logger.info(f"Types are: {np.unique(feature_type)}")

                #self.logger.info("Simplifying polygons...")
                #polygons = [poly.simplify(tolerance) for poly in
                #            tqdm(polygons, desc="Simplifying polygons", unit="polygon")]

                gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=src_steepness.crs)

                contour_filename = f'{res}_steepness_contour_{min_steepness}_{max_steepness}_{"_".join(sorted(orientations)) if orientations else ""}_{elevation_start or ""}_{elevation_end or ""}.shp'
                contour_path = os.path.join(self.path, 'managed', contour_filename)
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

        Returns:
            str: Path to the computed aspect raster file, or None if computation failed.
        """
        self.get_DEM(res)

        if not self.DEM_path:
            self.logger.error("DEM not available. Please download DEM first.")
            return

        self.logger.info(f"Starting computation of aspect raster from {self.DEM_path}")

        try:
            with rasterio.open(self.DEM_path) as src:
                elevation = src.read(1)
                profile = src.profile

                x_res = profile['transform'][0]
                y_res = -profile['transform'][4]

                self.logger.info("Calculating gradients...")
                gradient_x, gradient_y = np.gradient(elevation, x_res, y_res)
                aspect = np.arctan2(-gradient_y, gradient_x)
                aspect = np.rad2deg(aspect) % 360

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
            str: Path to the DEM file, or None if download failed.
        """
        if self.force or not self.DEM_path:
            self.logger.info("DEM not found or force flag is set. Downloading DEM...")
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
            str: Path to the steepness raster file, or None if computation failed.
        """
        if self.force or not self.steepness_raster_path:
            self.logger.info("Steepness raster not found or force flag is set. Computing steepness raster...")
            self._compute_steepness_raster(res)
        if not self.steepness_raster_path:
            self.logger.error("Steepness raster computation failed.")
            return None
        return self.steepness_raster_path

    def get_aspect_raster(self, res='DTM50'):
        """
        Gets the file path to the aspect raster, computing it if necessary.

        Args:
            res (str): The resolution of the DEM to use.

        Returns:
            str: Path to the aspect raster file, or None if computation failed.
        """
        aspect_filename = f'{res}_aspect_raster.tif'
        aspect_path = os.path.join(self.path, 'managed', aspect_filename)

        if self.force or not os.path.exists(aspect_path):
            self.logger.info("Aspect raster not found or force flag is set. Computing aspect raster...")
            aspect_path = self._compute_aspect_raster(res)
        else:
            self.logger.info(f"Aspect raster already exists at {aspect_path}")

        return aspect_path

    def get_steepness_contour(self, min_steepness, max_steepness, res='DTM50', orientations=None, elevation_start=None,
                              elevation_end=None):
        """
        Gets the file path to the steepness contour shapefile, creating it if necessary.

        Args:
            min_steepness (float): The minimum steepness value.
            max_steepness (float): The maximum steepness value.
            res (str): The resolution of the DEM to use.
            orientations (list, optional): The list of orientations to filter the contours by.
            elevation_start (float, optional): The minimum elevation value.
            elevation_end (float, optional): The maximum elevation value.

        Returns:
            str: Path to the steepness contour file, or None if creation failed.
        """
        contour_filename = f'{res}_steepness_contour_{min_steepness}_{max_steepness}_{"_".join(sorted(orientations)) if orientations else ""}_{elevation_start or ""}_{elevation_end or ""}.shp'
        contour_path = os.path.join(self.path, 'managed', contour_filename)

        self.logger.info(f"Checking for existing contour file at {contour_path}")

        if self.force or not os.path.exists(contour_path):
            self.logger.info(f"Contour file not found or force flag is set. Creating new contour file.")
            self.contour_path = self._create_steepness_contour(min_steepness, max_steepness, res, orientations,
                                                               elevation_start, elevation_end)
        else:
            self.logger.info(f"Steepness contour already exists at {contour_path}")
            self.contour_path = contour_path

        return self.contour_path

    def get_steepness_contour_direction(self, orientation, min_steepness=25, max_steepness=55, res='DTM50'):
        """
        Gets the file path to the steepness contour shapefile, creating it if necessary,
        optionally filtered by orientation.

        Args:
            orientation (str): The orientation to filter the contours by.
            min_steepness (float): The minimum steepness value.
            max_steepness (float): The maximum steepness value.
            res (str): The resolution of the DEM to use.

        Returns:
            str: Path to the steepness contour file, or None if creation failed.
        """
        contour_filename = f'{res}_steepness_contour_{min_steepness}_{max_steepness}_{orientation if orientation else ""}.shp'
        contour_path = os.path.join(self.path, 'managed', contour_filename)

        self.logger.info(f"Checking for existing contour file with orientation at {contour_path}")

        if self.force or not os.path.exists(contour_path):
            self.logger.info(f"Contour file with orientation not found or force flag is set. Creating new contour file.")
            self.contour_path = self._create_steepness_contour(min_steepness, max_steepness, res, orientation)
        else:
            self.logger.info(f"Steepness contour with orientation already exists at {contour_path}")
            self.contour_path = contour_path

        return self.contour_path