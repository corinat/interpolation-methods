# About the project
This Python project that performs point interpolation within a given polygon. By default, it uses world country boundaries from OpenStreetMap (OSM), but other boundaries can be used if needed. The point layer is automatically generated to fit within the selected boundaries.
Two interpolation python libraries are used: `scipy.interpolate` and `matplotlib.tri`.  

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
python run_interpolation_methods.py -l scipy -p ../multipolygons.shp -t ../random_points.gpkg -m linear  -o ../linear.tif
```
or
```bash
python run_interpolation_methods.py -l  mpl -p ../multipolygons.shp -t ../random_points.gpkg -m linear_tri_interpolator -o ../linear_mpl.tif
```

Interpolation method can be: `linear`, `cubic`, or `nearest` for `scipy`, 
or `linear_tri_interpolator`, `cubic_geom_min_e`, or `interp_cubic_geom` for `mpl`.  


### If the countries boundaries OSM file is not already downloaded, run the following bash commands:
```bash
run as: ./run_interpolation_methods.sh scipy ../multipolygons.shp ../random_points.gpkg linear ../linear_scipy.tif ../
```
or
```bash
./run_interpolation_methods.sh mpl ../multipolygons.shp ../random_points.gpkg linear_tri_interpolator ../linear_mpl.tif ../
```


