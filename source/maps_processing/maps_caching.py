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
    computing steepness and aspect rasters, and creating steepness contours.

    This class provides methods to handle DEM files, compute steepness and aspect rasters,
    and generate contour shapefiles based on steepness, orientation, and elevation criteria.
    It ensures that necessary files are downloaded or computed as needed and stored in a
    managed directory.

    Attributes:
        path (str): The base directory path for storing maps and related files.
        force (bool): Flag to force re-download and re-computation of files.
        DEM_res (dict): Dictionary mapping DEM resolutions to their respective download URLs.
        logger (Logger): Logger instance for logging messages.
        DEM_path (str): File path to the DEM file.
        steepness_raster_path (str): File path to the steepness raster file.
        contour_path (str): File path to the contour shapefile.

    Methods:
        __init__(path='./static/maps/', force=False):
            Initializes the MapsCaching instance and ensures the managed directory exists.

        _find_existing_DEM():
            Searches for an existing DEM file within the managed directory.

        _find_existing_steepness_raster():
            Searches for an existing steepness raster file within the managed directory.

        _find_existing_contour():
            Searches for an existing contour file within the managed directory.

        _download_DEM(res='DTM50'):
            Downloads a DEM file from a specified URL and extracts it.

        _compute_steepness_raster(res='DTM50'):
            Computes the steepness raster from a DEM file.

        _create_steepness_contour(min_steepness, max_steepness, res='DTM50', orientations=None, elevation_start=None, elevation_end=None):
            Creates a shapefile containing smoothed polygons that represent areas within a specified steepness range.

        _compute_aspect_raster(res='DTM50'):
            Computes the aspect raster from a DEM file.

        get_DEM(res='DTM50'):
            Retrieves the file path to the DEM, downloading it if necessary.

        get_steepness_raster(res='DTM50'):
            Retrieves the file path to the steepness raster, computing it if necessary.

        get_aspect_raster(res='DTM50'):
            Retrieves the file path to the aspect raster, computing it if necessary.

        get_steepness_contour(min_steepness, max_steepness, res='DTM50', orientations=None, elevation_start=None, elevation_end=None):
            Retrieves the file path to the steepness contour shapefile, creating it if necessary.

        get_steepness_contour_direction(orientation, min_steepness=25, max_steepness=55, res='DTM50'):
            Retrieves the file path to the steepness contour shapefile, creating it if necessary, optionally filtered by orientation.
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
        Searches for an existing Digital Elevation Model (DEM) file within the managed directory.

        This method iterates over the keys in the `DEM_res` dictionary, constructing filenames based on
        the resolution keys. It then checks the 'managed' subdirectory for files matching the constructed
        pattern and returns the path of the first matching file found.

        Returns:
            str or None: The file path of the existing DEM file if found. Returns None if no matching
                         DEM file is found in the managed directory.
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
        Searches for an existing steepness raster file within the managed directory.

        This method iterates over the keys in the `DEM_res` dictionary, constructing filenames based on
        the resolution keys. It then checks the 'managed' subdirectory for files matching the constructed
        filename pattern and returns the path of the first matching file found.

        Returns:
            str or None: The file path of the existing steepness raster file if found. Returns None if no
                         matching steepness raster file is found in the managed directory.
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
        Searches for an existing contour file within the managed directory.

        This method iterates over the files in the 'managed' subdirectory, looking for files that start
        with 'steepness_contour_' and end with the '.shp' extension. It returns the path of the first
        matching file found.

        Returns:
            str or None: The file path of the existing contour file if found. Returns None if no matching
                         contour file is found in the managed directory.
        """
        managed_path = os.path.join(self.path, 'managed')
        for file in os.listdir(managed_path):
            if file.startswith('steepness_contour_') and file.endswith('.shp'):
                return os.path.join(managed_path, file)
        return None

    def _download_DEM(self, res='DTM50'):
        """
        Downloads a Digital Elevation Model (DEM) file from a specified URL and extracts it.

        This method retrieves the URL associated with the given resolution from the `DEM_res` dictionary.
        It then downloads the file, displaying a progress bar, and extracts the contents to the 'managed'
        directory. The extracted `.tif` and `.txt` files are renamed to include the resolution in their
        filenames and moved to the appropriate location.

        Args:
            res (str): The resolution of the DEM to download. Defaults to 'DTM50'.

        Raises:
            requests.RequestException: If there is an error during the download process.
            zipfile.BadZipFile: If the downloaded file is not a valid zip file.
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
        Computes the steepness raster from a Digital Elevation Model (DEM) file.

        This method calculates the steepness (slope) of the terrain based on the elevation data from the DEM file.
        It reads the DEM file, computes the gradients in the x and y directions, and then calculates the slope
        in degrees. The resulting steepness raster is saved as a GeoTIFF file in the 'managed' directory.

        Args:
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.

        Raises:
            Exception: If there is an error during the computation or file handling process.
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
        Creates a shapefile containing smoothed polygons that represent areas within a specified steepness range.
        The polygons can be optionally filtered by orientation and elevation range.

        This method reads the steepness raster and applies filters based on the provided steepness range,
        orientation, and elevation range. It generates polygons for the areas that meet the criteria and
        simplifies them to reduce complexity. The resulting polygons are saved as a shapefile in the 'managed'
        directory.

        Args:
            min_steepness (float): The minimum steepness value in degrees.
            max_steepness (float): The maximum steepness value in degrees.
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.
            orientations (str or list of str, optional): The orientation(s) to filter the contours by.
            elevation_start (float, optional): The minimum elevation value in meters.
            elevation_end (float, optional): The maximum elevation value in meters.

        Returns:
            str or None: The file path of the created contour shapefile if successful, or None if creation failed.

        Raises:
            Exception: If there is an error during the contour creation process.
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

                self.logger.info("Simplifying polygons...")
                polygons = [poly.simplify(tolerance) for poly in
                            tqdm(polygons, desc="Simplifying polygons", unit="polygon")]

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
        Computes the aspect raster from a Digital Elevation Model (DEM) file.

        This method calculates the aspect (direction) of the terrain based on the elevation data from the DEM file.
        It reads the DEM file, computes the gradients in the x and y directions, and then calculates the aspect
        in degrees. The resulting aspect raster is saved as a GeoTIFF file in the 'managed' directory.

        Args:
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.

        Returns:
            str or None: The file path of the computed aspect raster file if successful, or None if computation failed.

        Raises:
            Exception: If there is an error during the computation or file handling process.
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
        Retrieves the file path to the Digital Elevation Model (DEM), downloading it if necessary.

        This method checks if the DEM file is already available or if the force flag is set. If the DEM is not
        available, it initiates the download process. If the download fails, it logs an error and returns None.

        Args:
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.

        Returns:
            str or None: The file path to the DEM file if available or successfully downloaded. Returns None if
                         the download fails or the DEM is not available.
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
        Retrieves the file path to the steepness raster, computing it if necessary.

        This method checks if the steepness raster is already available or if the force flag is set. If the steepness
        raster is not available, it initiates the computation process. If the computation fails, it logs an error and
        returns None.

        Args:
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.

        Returns:
            str or None: The file path to the steepness raster file if available or successfully computed. Returns None if
                         the computation fails or the steepness raster is not available.
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
        Retrieves the file path to the aspect raster, computing it if necessary.

        This method checks if the aspect raster is already available or if the force flag is set. If the aspect
        raster is not available, it initiates the computation process. If the aspect raster already exists, it
        logs a message indicating its location.

        Args:
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.

        Returns:
            str or None: The file path to the aspect raster file if available or successfully computed. Returns None if
                         the computation fails or the aspect raster is not available.
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
        Retrieves the file path to the steepness contour shapefile, creating it if necessary.

        This method checks if the steepness contour shapefile already exists or if the force flag is set. If the contour
        file is not available, it initiates the creation process. If the contour file already exists, it logs a message
        indicating its location.

        Args:
            min_steepness (float): The minimum steepness value in degrees.
            max_steepness (float): The maximum steepness value in degrees.
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.
            orientations (list of str, optional): The list of orientations to filter the contours by.
            elevation_start (float, optional): The minimum elevation value in meters.
            elevation_end (float, optional): The maximum elevation value in meters.

        Returns:
            str or None: The file path to the steepness contour shapefile if available or successfully created. Returns None if
                         the creation fails or the contour file is not available.
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
        Retrieves the file path to the steepness contour shapefile, creating it if necessary, optionally filtered by orientation.

        This method checks if the steepness contour shapefile with the specified orientation already exists or if the force
        flag is set. If the contour file is not available, it initiates the creation process. If the contour file already
        exists, it logs a message indicating its location.

        Args:
            orientation (str): The orientation to filter the contours by.
            min_steepness (float): The minimum steepness value in degrees. Defaults to 25.
            max_steepness (float): The maximum steepness value in degrees. Defaults to 55.
            res (str): The resolution of the DEM to use. Defaults to 'DTM50'.

        Returns:
            str or None: The file path to the steepness contour shapefile if available or successfully created. Returns None if
                         the creation fails or the contour file is not available.
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