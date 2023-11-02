from __future__ import annotations

import argparse
import logging

import dask.array as da
import geopandas as gpd
import numpy as np
import rasterio
from matplotlib.tri import CubicTriInterpolator, LinearTriInterpolator, Triangulation
from rasterio.transform import Affine
from scipy.interpolate import griddata


class GenerateRandomPointsAndInterpolate:
    @staticmethod
    def generate_random_points(polygon, points, points_number=200, epsg=4326):
        """Generate random points in polygon bbox

        Args:
            polygon: Path to polygon file, by default the format is gpkg
            points: Path to points file
            points_number (int, optional): Number of points generated. Defaults to 200000.
            epsg (int, optional): The epsg number. Defaults to 4326.
        """

        country_polygons = gpd.read_file(polygon)
        logging.info(f"Creating {points_number} random points")
        x_min, y_min, x_max, y_max = country_polygons.total_bounds
        x = np.random.uniform(x_min, x_max, points_number)
        y = np.random.uniform(y_min, y_max, points_number)
        gdf_points = gpd.GeoSeries(gpd.points_from_xy(x, y))
        gdf_points.crs = f"epsg:{epsg}"
        # Retrieve the points that intersect the polygon
        random_points = gpd.GeoDataFrame(geometry=gdf_points.geometry)
        spatial_join = gpd.sjoin(random_points, country_polygons, predicate="within", how="left")
        spatial_join.dropna(subset=["index_right"], how="all", inplace=True)
        logging.info(f"Saving point file {points}")
        spatial_join.to_file(points)

    def generate_point_grid(
        self,
        points,
        column="randon_num",
        min_rand_points=100000,
        max_rand_points=200000,
        raster_resolution=2,
    ):
        """Generate interpolation grid

        Args:
            points: Path to points file
            column (str, optional): The column name used to generate z values. Defaults to "randon_num".
            min_rand_points (int, optional): Lowest integers to be drawn from the distribution. Defaults to 100000.
            max_rand_points (int, optional): Heighest integers to be drawn from the distribution. Defaults to 200000.
            raster_resolution (int, optional): Resolution of the output raster. Defaults to 2.

        Returns:
            x y z grid parameters, total number of points in array and the geopandas column with z values
        """
        points3d = gpd.read_file(points)
        points3d[column] = np.random.randint(min_rand_points, max_rand_points, points3d.shape[0])

        # Get numpy array with XYZ point data

        total_points_array = np.zeros([points3d.shape[0], 3])
        for index, point in points3d.iterrows():
            pointArray = np.array(
                [
                    point.geometry.coords.xy[0][0],
                    point.geometry.coords.xy[1][0],
                    point[column],
                ]
            )
            total_points_array[index] = pointArray

        logging.info("Generating point grid")

        x_coords = np.arange(
            total_points_array[:, 0].min(),
            total_points_array[:, 0].max() + raster_resolution,
            raster_resolution,
        )
        y_coords = np.arange(
            total_points_array[:, 1].min(),
            total_points_array[:, 1].max() + raster_resolution,
            raster_resolution,
        )
        z_coords = np.zeros([y_coords.shape[0], x_coords.shape[0]])

        return x_coords, y_coords, z_coords, total_points_array, points3d[column]

    def create_dask_chunks(self, z_coords, chunk=100):
        """Using dask to generate the raster

        Args:
            z_coords: Z values of the array
            chunk (int, optional): Number of chunks to create. Defaults to 10.

        Returns:
            Dask array
        """
        logging.info(f"Creating dask {chunk} chunks")
        return da.from_array(z_coords, chunks=(chunk, chunk))

    def generate_affine_transform(self, x_coords, y_coords, raster_resolution):
        """Generates affine transformation matrix

        Args:
            x_coords: Coordinates for x
            y_coords: Coordinates for y
            raster_resolution: Raster resolution

        Returns:
            Affine transform matrix
        """
        logging.info("Generating affine transform")
        return Affine.translation(
            x_coords[0] - raster_resolution / 2, y_coords[0] - raster_resolution / 2
        ) * Affine.scale(raster_resolution, raster_resolution)

    def write_rast(self, array, z_coords, transform, out_raster, epsg=4326):
        """Writing output raster

        Args:
            array: Array that needs to written
            z_coords: Z values
            transform: Affine transform matrix
            out_raster: Path of output raster
            epsg (int, optional): Epsg number. Defaults to 4326.
        """

        profile = {
            "driver": "GTiff",
            "height": z_coords.shape[0],
            "width": z_coords.shape[1],
            "count": 1,
            "dtype": z_coords.dtype,
            "crs": {"init": f"epsg:{epsg}"},
            "compress": "lzw",
            "transform": transform,
            "nodata": np.nan,
        }

        logging.info(f"Writing raster: {out_raster}")
        with rasterio.open(out_raster, "w", **profile) as dst:
            dst.write(array, 1)

    def scipy_interpolation(
        self,
        points,
        out_raster,
        column="randon_num",
        raster_resolution=2,
        method="linear",
        fill_value=np.nan,
        rescale=False,
    ):
        """Interpolation based on Scipy library

        Args:
            points: Path to points file
            out_raster: Path to output raster
            column (str, optional): Column name with Z values. Defaults to "randon_num".
            raster_resolution (int, optional): Raster resolution. Defaults to 2.
            method (str, optional): Type of interpolatio: nearest, linear, cubic.
            Defaults to 'linear'.
        """

        logging.info("Running scipy interpolation method")
        points3d = gpd.read_file(points)
        x_coords, y_coords, z_coords, _, points3d[column] = self.generate_point_grid(points)

        points = [(x, y) for x, y in zip(points3d["geometry"].x, points3d["geometry"].y)]
        values = points3d[column].values

        grid_x, grid_y = np.meshgrid(x_coords, y_coords)
        grid_data = griddata(
            points,
            values,
            (grid_x, grid_y),
            method=method,
            fill_value=fill_value,
            rescale=rescale,
        )

        transform = self.generate_affine_transform(x_coords, y_coords, raster_resolution)
        array = self.create_dask_chunks(grid_data)
        self.write_rast(array, z_coords, transform, out_raster)

    def choose_interp_method(self, method, linear_tri_interpolator, interp_cubic_min_e, interp_cubic_geom):
        """Switching between matplotlib interpolation methods

        Args:
            method: Method name, can be one of linear_tri_interpolator, cubic_geom_min_e, interp_cubic_geom
            linear_tri_interpolator: Method type
            interp_cubic_min_e: Method type
            interp_cubic_geom: Method type

        Returns:
            Matplotlib interpolation methods linear_tri_interpolator, cubic_geom_min_e or interp_cubic_geom
        """
        if method == "linear_tri_interpolator":
            return linear_tri_interpolator
        elif method == "cubic_geom_min_e":
            return interp_cubic_min_e
        elif method == "interp_cubic_geom":
            return interp_cubic_geom

    def matplotlib_interpolation(
        self,
        points,
        out_raster,
        column="randon_num",
        raster_resolution=2,
        method="linear_tri_interpolator",
    ):
        """Matplotlib interpolation method

        Args:
            points: Path to points file
            out_raster: Path to output raster
            column (str, optional): Column name with Z values. Defaults to "randon_num".
            raster_resolution (int, optional): Raster resolution. Defaults to 2.
            method: Interpolation method, can be one of these: linear_tri_interpolator,
            cubic_geom_min_e or interp_cubic_geom
        """
        logging.info("Running matplotlib interpolation method")

        points3d = gpd.read_file(points)
        # Required elements for the triangular interpolation
        (
            x_coords,
            y_coords,
            z_coords,
            total_points_array,
            points3d[column],
        ) = self.generate_point_grid(points)
        # triangulation method
        triang = Triangulation(total_points_array[:, 0], total_points_array[:, 1])
        # linear triangule interpolator funtion
        linear_tri_interpolator = LinearTriInterpolator(triang, total_points_array[:, 2])
        # interpolator funtion Cubic interpolator on a triangular grid
        interp_cubic_min_e = CubicTriInterpolator(triang, total_points_array[:, 2], kind="min_E")
        interp_cubic_geom = CubicTriInterpolator(triang, total_points_array[:, 2], kind="geom")
        # Interpolated raster generation
        method = self.choose_interp_method(method, linear_tri_interpolator, interp_cubic_min_e, interp_cubic_geom)
        # loop among each cell in the raster extension
        for index_x, x in np.ndenumerate(x_coords):
            for index_y, y in np.ndenumerate(y_coords):
                temp_z = method(x, y)
                # filtering masked values
                if temp_z == temp_z:
                    z_coords[index_y, index_x] = temp_z
                else:
                    z_coords[index_y, index_x] = np.nan

        transform = self.generate_affine_transform(x_coords, y_coords, raster_resolution)
        array = self.create_dask_chunks(z_coords)
        self.write_rast(array, z_coords, transform, out_raster)

    def generate_argparse(self):
        """Generate argparse arguments

        Returns:
            Argparse arguments
        """
        my_parser = argparse.ArgumentParser(description="Running interpolation methods")

        my_parser.add_argument(
            "--interp_library",
            "-l",
            type=str,
            metavar="interp_library",
            required=True,
            help="The interpolation library to be used. Expected scipy or mpl.",
        )

        my_parser.add_argument(
            "--polygon_path",
            "-p",
            type=str,
            metavar="polygon_path",
            required=True,
            help="Path to the osm file. Expected a polygon shapefile",
        )
        my_parser.add_argument(
            "--points_path",
            "-t",
            type=str,
            metavar="points_path",
            required=True,
            help="Path to points file. Expected a point file, gpkg format",
        )
        my_parser.add_argument(
            "--interp_method",
            "-m",
            type=str,
            metavar="interp_method",
            required=True,
            help="Expected linear_tri_interpolator, cubic_geom_min_e or interp_cubic_geom for mpl or "
            "linear, cubic, nearest for scipy",
        )
        my_parser.add_argument(
            "--output_raster",
            "-o",
            required=True,
            metavar="output_raster",
            type=str,
            help="path to output raster",
        )
        my_parser.add_argument(
            "--download_osm",
            "-f",
            required=False,
            metavar="download_osm",
            type=str,
            help="Path to the location where the osm file will be downloaded. "
            "Argument used only when running the interpolation_methods.sh",
        )

        args = my_parser.parse_args()
        interp_library = args.interp_library
        polygon_path = args.polygon_path
        points_path = args.points_path
        interp_method = args.interp_method
        output_raster = args.output_raster
        download_osm = args.download_osm
        return (
            interp_library,
            polygon_path,
            points_path,
            interp_method,
            output_raster,
            download_osm,
        )
