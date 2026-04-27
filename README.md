# About the project
This Python project performs point interpolation within a given polygon, producing an interpolated raster (GeoTIFF) as output. By default it uses world country boundaries from OpenStreetMap (OSM), but any polygon file can be provided. The point layer is automatically generated to fit within the selected boundaries.
Two interpolation backends are supported: `scipy.interpolate` and `matplotlib.tri`.

## How it works

The pipeline runs in the following steps:

### 1. Random point generation (`generate_random_points`)
Given a polygon file (e.g. country boundaries), random points are generated within the bounding box of the polygon and then spatially filtered to keep only those that fall **within** the polygon. Each point is assigned a random numeric z-value (between 100,000 and 200,000 by default). The result is saved as a GeoPackage (`.gpkg`).

By default **200 points** are generated. This can be overridden with the `--points_number` / `-n` option when running the Python script:
```bash
python src/run_interpolation_methods.py -l scipy -p /usr/src/app/data/multipolygons.shp -t /usr/src/app/data/random_points.gpkg -m linear -o /usr/src/app/data/linear.tif -n 500
```

### 2. Regular grid generation (`RasterInterpolator.generate_point_grid`)
The spatial extent of the point cloud is used to build a regular x/y grid at a fixed cell resolution (default: 2 CRS units per cell). Each point is also assigned a fresh random z-value at this stage, which is used as the value to interpolate.

### 3. Interpolation
The scattered point values are interpolated onto the regular grid using one of two backends:

#### SciPy (`scipy.interpolate.griddata`)
Uses `griddata` to fill the grid. Supported methods:
| Method | Description |
|--------|-------------|
| `linear` | Piecewise linear interpolation (Delaunay triangulation) |
| `cubic` | Piecewise cubic interpolation |
| `nearest` | Nearest-neighbour interpolation |

#### Matplotlib (`matplotlib.tri.Triangulation`)
Triangulates the point cloud and evaluates an interpolator on the meshgrid. Supported methods:
| Method | Description |
|--------|-------------|
| `linear_tri_interpolator` | Linear interpolation on the triangulation |
| `cubic_geom_min_e` | Cubic interpolation minimising energy (`kind='min_E'`) |
| `interp_cubic_geom` | Cubic interpolation using geometric approach (`kind='geom'`) |

### 4. Raster output (`RasterInterpolator.write_rast`)
The interpolated grid is written to a single-band, LZW-compressed GeoTIFF with:
- CRS: EPSG:4326 (default)
- Nodata: `NaN`
- Affine transform centred on pixel centres

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
python src/run_interpolation_methods.py -l scipy -p /usr/src/app/data/multipolygons.shp -t /usr/src/app/data/random_points.gpkg -m linear  -o /usr/src/app/data/linear.tif
```
or
```bash
python src/run_interpolation_methods.py -l  mpl -p /usr/src/app/data/multipolygons.shp -t /usr/src/app/data/random_points.gpkg -m linear_tri_interpolator -o /usr/src/app/data/linear_mpl.tif
```

Interpolation method can be: `linear`, `cubic`, or `nearest` for `scipy`, 
or `linear_tri_interpolator`, `cubic_geom_min_e`, or `interp_cubic_geom` for `mpl`.  


### If the countries boundaries OSM file is not already downloaded, run the following bash commands:
```bash
run as: ./src/run_interpolation_methods.sh scipy /usr/src/app/data/multipolygons.shp /usr/src/app/data/random_points.gpkg linear /usr/src/app/linear_scipy.tif /usr/src/app/data/
```
or
```bash
./src/run_interpolation_methods.sh mpl /usr/src/app/data/multipolygons.shp /usr/src/app/data/random_points.gpkg linear_tri_interpolator /usr/src/app/data/linear_mpl.tif /usr/src/app/data/
```


