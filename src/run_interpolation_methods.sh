#!/bin/bash

# run as: ./run_interpolation_methods.sh scipy $HOME/quarticle/data/multipolygons.shp $HOME/quarticle/data/random_points.gpkg linear $HOME/quarticle/data/linear_scipy.tif $HOME/quarticle/data/
# or
# ./run_interpolation_methods.sh mpl $HOME/quarticle/data/multipolygons.shp $HOME/quarticle/data/random_points.gpkg linear_tri_interpolator $HOME/quarticle/data/linear_mpl.tif $HOME/quarticle/data/

STARTTIME=$(date +%s)

# activate conda environment
eval "$(conda shell.bash hook)"
conda activate venv3.8-bis

interp_library=$1 # the interpolation library to be used. Expected scipy or mpl.
polygon_path=$2 # path to osm polygon file
points_path=$3 # path to points file
interp_method=$4 # interpolation method. Expected linear_tri_interpolator, cubic_geom_min_e or interp_cubic_geom for mpl or linear, cubic, nearest for scipy
output_raster=$5 # path to output raster
download_osm=$6 # path to where the osm file will be saved

echo ""
echo "-------Downloading OSM - countries boundaries to ${download_osm}countries-border.osm----------"
echo ""
curl \
  --connect-timeout 10  \
  --retry 10  \
  --retry-delay 10  \
  --retry-max-time 500  \
  -H "Host: overpass-api.de" -H "Content-Type: text/xml"  \
  -d 'relation["admin_level"="2"];(._;>;); out body;'  \
  http://overpass-api.de/api/interpreter  \
  -o ${download_osm}countries-border.osm

echo ""
echo "-------Converting osm data to shapefile--------"
echo ""
ogr2ogr -f "ESRI Shapefile" -skipfailures $download_osm ${download_osm}countries-border.osm

echo ""
echo "------Running interpolation script-------"
echo ""

python ${HOME}/quarticle/src/run_interpolation_methods.py -l $interp_library -p $polygon_path -t $points_path -m $interp_method -o $output_raster

ENDTIME=$(date +%s)
echo "Duration to complete: $((($ENDTIME - $STARTTIME)/60))m and $(($ENDTIME - $STARTTIME))s"
