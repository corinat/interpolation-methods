import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from methods.interpolate_methods import RasterInterpolator, generate_random_points

app = typer.Typer()
class_instance = RasterInterpolator()


@app.command()
def run_interpolation(
    interpolation_library: Annotated[str, typer.Option("--interp_library", "-l", help="Interpolation library: scipy or mpl.")],
    polygon_path: Annotated[str, typer.Option("--polygon_path", "-p", help="Path to the polygon file.")],
    points_path: Annotated[str, typer.Option("--points_path", "-t", help="Path to the points file (gpkg format).")],
    interp_method: Annotated[str, typer.Option("--interp_method", "-m", help="Interpolation method.")],
    output_raster: Annotated[str, typer.Option("--output_raster", "-o", help="Path to the output raster.")],
    download_osm: Annotated[str | None, typer.Option("--download_osm", "-f", help="Path where the OSM file will be saved (used by the bash script only.")] = None,
    points_number: Annotated[int, typer.Option("--points_number", "-n", help="Number of random points to generate within the polygon.")] = 200,
) -> None:
    """Run the interpolation pipeline on a set of points within a polygon."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    Path(polygon_path).parent.mkdir(parents=True, exist_ok=True)
    Path(points_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_raster).parent.mkdir(parents=True, exist_ok=True)

    if not Path(polygon_path).exists():
        logging.info(f"The polygon path does not exist: {Path(polygon_path).resolve()}")
        raise typer.Exit(code=1)

    start_time = datetime.now()
    logging.info(f"Running {interp_method} interpolation method from {interpolation_library} library")

    generate_random_points(polygon=polygon_path, points=points_path, points_number=points_number)
    if interpolation_library == "mpl":
        class_instance.matplotlib_interpolation(points=points_path, out_raster=output_raster, method=interp_method)
    elif interpolation_library == "scipy":
        class_instance.scipy_interpolation(points=points_path, out_raster=output_raster, method=interp_method)
    else:
        logging.error(f"Unknown interpolation library: {interpolation_library!r}. Expected 'scipy' or 'mpl'.")
        raise typer.Exit(code=1)

    end_time = datetime.now()
    logging.info(f"Duration: {end_time - start_time}")


if __name__ == "__main__":
    app()
