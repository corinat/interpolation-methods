# About the project
This Python project that performs point interpolation within a given polygon. By default, it uses world country boundaries from OpenStreetMap (OSM), but other boundaries can be used if needed. The point layer is automatically generated to fit within the selected boundaries, with the number of points passed in the code as a default value ifa number is not specified via the command line.
Two interpolation Python libraries are used: `scipy.interpolate` and `matplotlib.tri`.  

## Environment
The project runs in a Docker container, with commands specified in the `Makefile`.

Code is linted using `flake8` with `--max-line-length=120`.  
Code formatting is validated using `Black`.  
`pre-commit` is used to run these checks locally before files are pushed to Git.  
The GitHub Actions pipeline also runs these checks.  

## Running the code
To view the required parameters, run: python run_interpolation_methods.py --help


### If the OSM file with polygons is already downloaded, run the following python commands:  
```bash
python run_interpolation_methods.py -l interpolation_library -p path_to_osm_polygons -t path_to_points -m method_type -o path_to_output_raster
```

`interpolation_library` can be: `scipy` or `mpl`.
`method_type` can be: `linear`, `cubic`, or `nearest` for `scipy`, 
or `linear_tri_interpolator`, `cubic_geom_min_e`, or `interp_cubic_geom` for `mpl`.  


### If the countries boundaries OSM file is not already downloaded, run the following bash commands:
```bash
run as: ./run_interpolation_methods.sh scipy /usr/src/app/multipolygons.shp /usr/src/app/random_points.gpkg linear /usr/src/app/linear_scipy.tif /usr/src/app/
```
or
```bash
./run_interpolation_methods.sh mpl /usr/src/app/multipolygons.shp /usr/src/app/random_points.gpkg linear_tri_interpolator /usr/src/app/linear_mpl.tif /usr/src/app/
```


