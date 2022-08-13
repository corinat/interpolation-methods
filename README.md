# Interpolation methods

A valid GDAL/OGR installation is required, this can be achieved using your package manager of choice (e.g. apt, conda). Once this is installed, set up a new clean virtual environment and install the requirements:

```shell
# install gdal, e.g.
# apt install libgdal-dev
# conda install gdal -c conda-forge

# create new virtualenv and install reqs
mkvirtualenv --python=/usr/bin/python3.8 venv3.8
pip install -r requirements-dev.txt
pip install -r requirements.txt
pip install -e .
pre-commit install
```

- Code is linted using [flake8](https://flake8.pycqa.org/en/latest/) with `--max-line-length=120`
- Code formatting is validated using [Black](https://github.com/psf/black)
- [pre-commit](https://pre-commit.com/) is used to run these checks locally before files are pushed to git
- The [Github Actions pipeline](.github/workflows/pipeline.yml) also runs these checks

Two interpolation python libraries have been used, `scipy.interpolate` and `matplotlib.tri`

Interpolation methods are run as: `python run_interpolation_methods.py -l interpolation_library -p path_to_osm_polygons -t path_to_points -m method_type -t path_to_output_raster` if the osm file with polygons is already downloaded

Or run: `./run_interpolation_methods.sh interpolation_library path_to_osm_polygons path_to_points method_type path_to_output_raster number_of_random_points raster_resolution path_to_osm_file` if the osm file still needs to be downloaded.

`method_type` can be:
`linear, cubic or nearest` for `scipy`
or
`linear_tri_interpolator, cubic_geom_min_e or interp_cubic_geom` for `mpl`.

`interpolation_library` can be: `scipy` or `mpl`
