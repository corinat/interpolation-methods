import logging
import sys
from datetime import datetime
from pathlib import Path

from methods.interpolate_methods import GenerateRandomPointsAndInterpolate

class_instance = GenerateRandomPointsAndInterpolate()


def run_interpolation(
    interpolation_library,
    polygon_path,
    points_path,
    interp_method,
    output_raster,
    download_osm,
):
    class_instance.generate_random_points(polygon=polygon_path, points=points_path)
    if interpolation_library == "mpl":
        return class_instance.matplotlib_interpolation(
            points=points_path, out_raster=output_raster, method=interp_method
        )
    elif interpolation_library == "scipy":
        return class_instance.scipy_interpolation(points=points_path, out_raster=output_raster, method=interp_method)


if __name__ == "__main__":
    (
        interp_library,
        polygon_path,
        points_path,
        interp_method,
        output_raster,
        download_osm,
    ) = class_instance.generate_argparse()

    if not Path(polygon_path).exists():
        logging.info("The path specified does not exist")
        sys.exit()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    start_time = datetime.now()
    logging.info(f"Running {interp_method} interpolation method from {interp_library} library")
    run_interpolation(
        interp_library,
        polygon_path,
        points_path,
        interp_method,
        output_raster,
        download_osm,
    )
    end_time = datetime.now()
    logging.info(f"Duration: {end_time - start_time}")
