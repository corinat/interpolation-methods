# This Python library performs point interpolation within a given polygon. By default, it uses world country boundaries from OpenStreetMap (OSM), but other boundaries can be used if needed. The point layer is automatically generated to fit within the selected boundaries, with the number of points specified via the command line.


## Environment
The project runs in a Docker container, with commands specified in the Makefile.

Code is linted using `flake8` with `--max-line-length=120`.  
Code formatting is validated using `Black`.  
`pre-commit` is used to run these checks locally before files are pushed to Git.  
The GitHub Actions pipeline also runs these checks.  


## Examples of how to run the script
Two interpolation Python libraries have been used: `scipy.interpolate` and `matplotlib.tri`.  

### If the OSM file with polygons is already downloaded.  
```bash
python run_interpolation_methods.py -l interpolation_library -p path_to_osm_polygons -t path_to_points -m method_type -o path_to_output_raster
```

### If the OSM file with polygons is not already downloaded:

```bash
run as: ./run_interpolation_methods.sh scipy /usr/src/app/multipolygons.shp /usr/src/app/random_points.gpkg linear /usr/src/app/linear_scipy.tif /usr/src/app/
```
or
```bash
./run_interpolation_methods.sh mpl /usr/src/app/multipolygons.shp /usr/src/app/random_points.gpkg linear_tri_interpolator /usr/src/app/linear_mpl.tif /usr/src/app/
```

To view the required parameters, run: ython run_interpolation_methods.py --help
`method_type` can be: `linear`, `cubic`, or `nearest` for `scipy`, or `linear_tri_interpolator`, `cubic_geom_min_e`, or `interp_cubic_geom` for `mpl`.  
`interpolation_library` can be: `scipy` or `mpl`.
