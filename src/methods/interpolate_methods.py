
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from matplotlib.tri import CubicTriInterpolator, LinearTriInterpolator, Triangulation
from rasterio.transform import Affine
from scipy.interpolate import griddata


class RasterInterpolator:
    """Interpolates scattered point data onto a regular raster grid.

    Supports two interpolation backends:
    - SciPy (``griddata``): nearest, linear, cubic methods.
    - Matplotlib (``Triangulation``): linear, cubic min-energy, cubic geometric methods.

    Typical usage::

        interpolator = RasterInterpolator()
        interpolator.scipy_interpolation(points="points.gpkg", out_raster="out.tif")
    """

    def generate_point_grid(
        self,
        points: str | Path,
        column: str = "randon_num",
        min_rand_points: int = 100000,
        max_rand_points: int = 200000,
        raster_resolution: int = 2,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.Series]:
        """Generate a regular x/y grid spanning the extent of the input points.

        Reads the point file, assigns random z-values in [min_rand_points, max_rand_points),
        and computes the 1-D coordinate arrays and empty z-grid that cover the point cloud
        extent at the requested resolution.

        Args:
            points: Path to the input point file (any format readable by geopandas).
            column: Name of the column to store generated z values. Defaults to "randon_num".
            min_rand_points: Lower bound (inclusive) for random z values. Defaults to 100000.
            max_rand_points: Upper bound (exclusive) for random z values. Defaults to 200000.
            raster_resolution: Cell size of the output grid in CRS units. Defaults to 2.

        Returns:
            Tuple of (x_coords, y_coords, z_coords, total_points_array, z_series):
            - x_coords: 1-D array of x grid coordinates.
            - y_coords: 1-D array of y grid coordinates.
            - z_coords: 2-D zeros array shaped (len(y_coords), len(x_coords)).
            - total_points_array: (N, 3) array of [x, y, z].
            - z_series: Series of z values assigned to each point.
        """
        points3d = gpd.read_file(points)
        points3d[column] = np.random.randint(min_rand_points, max_rand_points, points3d.shape[0])

        logging.info("Generating point grid")
        total_points_array = np.stack(
            [
                points3d.geometry.x.values,
                points3d.geometry.y.values,
                points3d[column].values,
            ],
            axis=1,
        )

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

    def generate_affine_transform(
        self,
        x_coords: np.ndarray,
        y_coords: np.ndarray,
        raster_resolution: int,
    ) -> Affine:
        """Compute an Affine transformation matrix for the output raster.

        The translation is offset by half a pixel so that coordinates refer to
        cell centres rather than the top-left corner.

        Args:
            x_coords: 1-D array of x grid coordinates.
            y_coords: 1-D array of y grid coordinates.
            raster_resolution: Cell size in CRS units.

        Returns:
            Affine transformation matrix mapping pixel indices to CRS coordinates.
        """
        logging.info("Generating affine transform")
        return Affine.translation(
            x_coords[0] - raster_resolution / 2, y_coords[0] - raster_resolution / 2
        ) * Affine.scale(raster_resolution, raster_resolution)

    def write_rast(
        self,
        array: np.ndarray,
        z_coords: np.ndarray,
        transform: Affine,
        out_raster: str | Path,
        epsg: int = 4326,
    ) -> None:
        """Write a 2-D numpy array to a single-band GeoTIFF.

        The output is LZW-compressed with NaN as the nodata value.

        Args:
            array: 2-D numpy array to write as band 1.
            z_coords: 2-D array used to determine output raster height and width.
            transform: Affine transformation matrix for the raster.
            out_raster: Destination path for the output GeoTIFF.
            epsg: EPSG code for the output CRS. Defaults to 4326.
        """

        profile = {
            "driver": "GTiff",
            "height": z_coords.shape[0],
            "width": z_coords.shape[1],
            "count": 1,
            "dtype": z_coords.dtype,
            "crs": rasterio.crs.CRS.from_epsg(epsg),
            "compress": "lzw",
            "transform": transform,
            "nodata": np.nan,
        }

        logging.info(f"Writing raster: {out_raster}")
        with rasterio.open(out_raster, "w", **profile) as dst:
            dst.write(array, 1)

    def scipy_interpolation(
        self,
        points: str | Path,
        out_raster: str | Path,
        column: str = "randon_num",
        raster_resolution: int = 2,
        method: str = "linear",
        fill_value: float = np.nan,
        rescale: bool = False,
    ) -> None:
        """Interpolate scattered points onto a regular grid using SciPy's griddata.

        Reads points, generates a regular grid via ``generate_point_grid``, runs
        ``scipy.interpolate.griddata``, and writes the result to a GeoTIFF.

        Args:
            points: Path to the input point file (any format readable by geopandas).
            out_raster: Destination path for the output GeoTIFF.
            column: Column name containing z values. Defaults to "randon_num".
            raster_resolution: Cell size of the output grid in CRS units. Defaults to 2.
            method: Interpolation method — one of ``nearest``, ``linear``, ``cubic``.
                Defaults to ``linear``.
            fill_value: Value for grid cells outside the convex hull of the points.
                Defaults to ``np.nan``.
            rescale: If True, rescale x/y to the unit interval before interpolation.
                Defaults to False.
        """

        logging.info("Running scipy interpolation method")
        points3d = gpd.read_file(points)
        x_coords, y_coords, z_coords, _, points3d[column] = self.generate_point_grid(points)

        point_coords = list(zip(points3d["geometry"].x, points3d["geometry"].y))
        values = points3d[column].values

        grid_x, grid_y = np.meshgrid(x_coords, y_coords)
        grid_data = griddata(
            point_coords,
            values,
            (grid_x, grid_y),
            method=method,
            fill_value=fill_value,
            rescale=rescale,
        )

        transform = self.generate_affine_transform(x_coords, y_coords, raster_resolution)
        self.write_rast(grid_data, z_coords, transform, out_raster)

    def choose_interp_method(
        self,
        method: str,
        linear_tri_interpolator: LinearTriInterpolator,
        interp_cubic_min_e: CubicTriInterpolator,
        interp_cubic_geom: CubicTriInterpolator,
    ) -> LinearTriInterpolator | CubicTriInterpolator:
        """Select a Matplotlib triangular interpolator by name.

        Args:
            method: Interpolator name — one of ``linear_tri_interpolator``,
                ``cubic_geom_min_e``, or ``interp_cubic_geom``.
            linear_tri_interpolator: A ``LinearTriInterpolator`` instance.
            interp_cubic_min_e: A ``CubicTriInterpolator`` with ``kind='min_E'``.
            interp_cubic_geom: A ``CubicTriInterpolator`` with ``kind='geom'``.

        Returns:
            The selected interpolator instance.

        Raises:
            ValueError: If ``method`` is not one of the three recognised names.
        """
        if method == "linear_tri_interpolator":
            return linear_tri_interpolator
        elif method == "cubic_geom_min_e":
            return interp_cubic_min_e
        elif method == "interp_cubic_geom":
            return interp_cubic_geom
        else:
            raise ValueError(
                f"Unknown interpolation method: {method!r}. "
                "Expected one of: linear_tri_interpolator, cubic_geom_min_e, interp_cubic_geom"
            )

    def matplotlib_interpolation(
        self,
        points: str | Path,
        out_raster: str | Path,
        column: str = "randon_num",
        raster_resolution: int = 2,
        method: str = "linear_tri_interpolator",
    ) -> None:
        """Interpolate scattered points onto a regular grid using Matplotlib triangulation.

        Reads points, generates a regular grid via ``generate_point_grid``, triangulates
        the point cloud, evaluates the chosen interpolator on a meshgrid in a single
        vectorized call, and writes the result to a GeoTIFF.

        Args:
            points: Path to the input point file (any format readable by geopandas).
            out_raster: Destination path for the output GeoTIFF.
            column: Column name containing z values. Defaults to "randon_num".
            raster_resolution: Cell size of the output grid in CRS units. Defaults to 2.
            method: Interpolation method — one of ``linear_tri_interpolator``,
                ``cubic_geom_min_e``, or ``interp_cubic_geom``.
                Defaults to ``linear_tri_interpolator``.
        """
        logging.info("Running matplotlib interpolation method")

        points3d = gpd.read_file(points)
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
        interp_fn = self.choose_interp_method(method, linear_tri_interpolator, interp_cubic_min_e, interp_cubic_geom)
        grid_x, grid_y = np.meshgrid(x_coords, y_coords)
        z_flat = interp_fn(grid_x.ravel(), grid_y.ravel())
        z_coords = np.ma.filled(np.ma.masked_invalid(z_flat.reshape(grid_x.shape)), np.nan)
        transform = self.generate_affine_transform(x_coords, y_coords, raster_resolution)
        self.write_rast(z_coords, z_coords, transform, out_raster)


def generate_random_points(
    polygon: str | Path,
    points: str | Path,
    points_number: int = 200,
    epsg: int = 4326,
) -> None:
    """Generate random points within a polygon and save them to a file.

    Random x/y coordinates are sampled uniformly within the bounding box of the
    polygon, then spatially filtered to keep only those that fall within the polygon.
    The result is saved as a GeoPackage (or any format supported by geopandas).

    Args:
        polygon: Path to the polygon file used as the spatial boundary.
        points: Destination path for the output point file (gpkg format).
        points_number: Number of random points to generate before spatial filtering.
            Defaults to 200.
        epsg: EPSG code for the output CRS. Defaults to 4326.
    """
    country_polygons = gpd.read_file(polygon)
    logging.info(f"Creating {points_number} random points")
    x_min, y_min, x_max, y_max = country_polygons.total_bounds
    x = np.random.uniform(x_min, x_max, points_number)
    y = np.random.uniform(y_min, y_max, points_number)
    gdf_points = gpd.GeoSeries(gpd.points_from_xy(x, y))
    gdf_points.crs = f"epsg:{epsg}"
    random_points = gpd.GeoDataFrame(geometry=gdf_points.geometry)
    spatial_join = gpd.sjoin(random_points, country_polygons, predicate="within", how="left")
    spatial_join.dropna(subset=["index_right"], how="all", inplace=True)
    logging.info(f"Saving point file {points}")
    spatial_join.to_file(points)
