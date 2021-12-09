#!/usr/bin/env python
# coding: utf-8

# ### Load Library
import os
import datetime
import shutil

from osgeo import ogr, gdal
import rasterio as rio
from rasterio.mask import mask
import pandas as pd
import geopandas as gpd
import numpy as np
import georasters as gr
import json
import fiona
from fiona.crs import from_epsg
from shapely.geometry import box

# for plotting
from rasterio import plot
from rasterio.plot import show
from rasterio.plot import show_hist
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx

# This will import all of the utility functions and more
from fldimpact_def import *

# Set working directory
# path = input("Insert path for your working directory:\t")
path = "/Users/evan/flood_map_py/"
os.chdir(path)
print("Current Working Directory ", os.getcwd())

#####################################################################################################
# Load up croplands raster dataset path
croplands_path = "Peru/croplands_S10W80.tif"

# Load up population raster dataset path
pop_path = "Peru/worldpop_peru.tif"

# Load up the OpenSteetMap point shapefile dataset path
osm_file = "Peru/Chazuta_points.shp"
#####################################################################################################

newpath = path + 'temp'
if not os.path.exists(newpath):
    os.makedirs(newpath)

for filename in os.listdir(newpath):
    file_path = os.path.join(newpath, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))

# Setting consistent plotting style throughout notebook
sns.set_style("dark")
sns.set(font_scale=1.5)
plot_title = "" #input("What is the name of the flooded area?\t")
begin_time = datetime.datetime.now()

#####################################################################################################
# Upload the flood map

# A single .shp file upload
# These are just file paths on Evan's computer change as you want
# flood_file = input("File path for the flood map shapefile:")
# flood_file = "Thailand_Oct2021/fld_poly_thai_100m.shp"
# flood_file = "Colombia/Inirida_flood_maps/Inirida_crs_4326/Inirida_crs_10Aug18_SRH2D.shp"
flood_file = "Peru/Chazuta_HAND_10m.shp"
flood_map = gpd.read_file(flood_file)
new_crs = flood_map.crs


'''
# This is to get flood extent map shapefile from a geodatabase

# for reading a geodatabase for shapefiles like from ArcGIS Pro
#floodmap_gdb = input("Put in the path of your geodatabase:\t")  #"Chazuta_test.gdb"
floodmap_gdb = "Chazuta_test.gdb"
layer = fiona.listlayers(floodmap_gdb)
print(layer)

#layer_file = input("Type the layer you would like to use from the printed layer text:\t")
layer_file = input("What flood would you like?:\t")
for layer in layer:
    flood_map = gpd.read_file(floodmap_gdb, layer = layer_file)
flood_map
new_crs = flood_map.crs'''
#####################################################################################################

# ### Force the CRS to be the same as the metric data (this case ESPG:4236)

# Since the data we have is in ESPG: 4326, force the shapefile to be same projection if not already there
if flood_map.crs == "EPSG:4326":
    pass
else:
    # Change the Coordinate Reference System to epsg=4326
    data = flood_map.to_crs(epsg=4326)

    # write shp file in the temp folder
    data.to_file('temp/fld_poly.shp')

    # Change the flood_map variable to be new shapefile location
    flood_map = gpd.read_file('temp/fld_poly.shp')
    new_crs = flood_map.crs


# Save the shapefile polygon to a geojson file to be saved for the SQL database

'''geojson_file = input("Name of the GeoJSON file:")
geojson_path = 'temp/' + geojson_file + '.geojson' '''
geojson_path = 'temp/fld_poly_test.geojson'
flood_map.to_file(geojson_path, driver='GeoJSON')
f = open('temp/fld_poly_test.geojson',)

fld_json = json.load(f)

#####################################################################################################
# ## Croplands Raster Data
# Clip raster data to the extent of the flood map.
# Display raster data in Rasterio with flood map on same plot.

# Load up future clipped raster file path
crop_clip = "temp/crop_clipped.tif"

ras2shp_extent(croplands_path, flood_map, crop_clip)

# ### Using GDAL, leave only the cell value 2 and delete all other cells

# Load up future reclassified raster file path
reclass_file = "temp/crop_reclass.tif"

reclass_raster(crop_clip, reclass_file, 2, 2, 2, 0)

# Load up future null raster file path
null_file = "temp/crop_null.tif"

ras_Null(reclass_file, null_file, 0)

# ## Convert Raster to Point Data
# Going to convert raster data to spatial point data frame. Will use .to_pandas() function of GeoRasters package.

# Data already loaded in variable filename

data = gr.from_file(null_file)

# Convert to Pandas DataFrame
single_df = data.to_pandas()
single_df.head()

# Drop some columns
columns = ['row', 'col', 'value']
single_df = pd.DataFrame(single_df.drop(columns=columns))
single_df["Hectares"] = 0.09
single_df = single_df[['x', 'y', 'Hectares']]  # organize column
single_df.head()


# Sequence to make Raster to Point Shapefile

# Load up future shapefile path
crop_pts = "temp/crop_pts.shp"

# Write as CVS file
single_df.to_csv(str(crop_pts.partition('.')[0] + '.csv'), index=None, header=True)

# Convert PD dataframe to Geopandas data frame
single_df_point = gpd.GeoDataFrame(
    single_df, geometry=gpd.points_from_xy(single_df.x, single_df.y))

# Define Projection
single_df_point.crs = {'init': new_crs}

# Writes as point shapefile
single_df_point.to_file(crop_pts)

cpts = gpd.read_file(crop_pts)

# Intersect the points with the flood map
clipped_ag = gpd.clip(cpts, flood_map)

# Obtain total hectares of agriculture in flooded area
hectares = clipped_ag['Hectares'].sum()

# Create geojson for ag
ag_geojson_path = 'temp/ag_poly.geojson'
clipped_ag.to_file(ag_geojson_path, driver='GeoJSON')
f = open('temp/ag_poly.geojson', )

ag_json = json.load(f)

#####################################################################################################
# ## Population Raster Dataset
# This will be similar to the croplands dataset process. We just want the total population within the inundation area.

# Load up future clipped raster file path
pop_clip = "temp/pop_clipped.tif"

ras2shp_extent(pop_path, flood_map, pop_clip)

# ## Converting raster to point datafile
# Data already loaded in variable pop_path
data = gr.from_file(pop_clip)

# Convert to Pandas DataFrame
pop_df = data.to_pandas()

# Drop some columns and rename others
columns =['row','col']
pop_df = pd.DataFrame(pop_df.drop(columns=columns))
pop_df.rename(columns = {'value':'Population'}, inplace = True)
pop_df = pop_df[['x','y','Population']] # organize column
pop_df = pop_df.astype({'Population': int})
pop_df.head()

# ### Load up the future population shapefile path
pop_pts = "temp/pop_pts.shp"

# Write as CVS file
pop_df.to_csv(str(pop_pts.partition('.')[0] + '.csv'), index=None, header=True)

# Convert PD dataframe to Geopandas data frame
pop_df_point = gpd.GeoDataFrame(
    pop_df, geometry=gpd.points_from_xy(pop_df.x, pop_df.y))

# Define projection
pop_df_point.crs = new_crs

# Writes as point shape file
pop_df_point.to_file(pop_pts)

popct = gpd.read_file(pop_pts)

# Intersect the points with the flood map
clipped_pop = gpd.clip(popct, flood_map)

# Get total population in flooded area
pop_count = clipped_pop['Population'].sum().astype(int)

# Create geojson for pop
pop_geojson_path = 'temp/pop_poly.geojson'
clipped_pop.to_file(pop_geojson_path, driver='GeoJSON')
f = open('temp/pop_poly.geojson', )

pop_json = json.load(f)

#####################################################################################################
# ## OpenStreetMap Shapefile Dataset
osm_pts = gpd.read_file(osm_file)

# Intersect the points with the flood map
osm_cl_df = gpd.clip(osm_pts, flood_map)

# Plot the points on the flood map
if osm_cl_df.empty:
    print("No amenities in the flooded area!")
else:
    osm_geojson_path = 'temp/osm_poly.geojson'
    osm_cl_df.to_file(osm_geojson_path, driver='GeoJSON')
    f = open('temp/osm_poly.geojson', )

    osm_json = json.load(f)

# It is possible that the dataframe is empty so this is a conditional argument for that
if osm_cl_df.empty:
    amen_ct = 0
    amen_gp_ct = 0
else:
    # Use a regular expression to extract what the amenity is
    # Store the amenity is a new column called Amenity
    osm_cl_df['Amenity'] = osm_cl_df['other_tags'].str.extract('"amenity"=>"(.+?)"').astype(str)

    ######################################
    # Drop some columns and rename others
    ######################################
    columns = ['osm_id', 'name', 'barrier', 'highway', 'ref', 'address', 'is_in', 'place', 'man_made', 'other_tags']
    osm_cl_df = gpd.GeoDataFrame(osm_cl_df.drop(columns=columns))

    # Delete rows that are of value 'nan' in Amenity column
    osm_cl_df = osm_cl_df[osm_cl_df.Amenity != 'nan']

    # Create a new column for the amenity group
    osm_cl_df["Amenity_Group"] = osm_cl_df.apply(lambda row: amen_group(row.Amenity), axis=1)

    # This converts the dataframe to a geodataframe and therefore can be plotted
    osm_cl_df = gpd.GeoDataFrame(osm_cl_df, geometry='geometry')

    # Store the list and values of the Amenities and Amenity Groups
    amen_ct = osm_cl_df["Amenity"].value_counts()
    amen_gp_ct = osm_cl_df["Amenity_Group"].value_counts()


#####################################################################################################
'''
# Let us graph stuff

# Plot Flood Extent area without flood (alpha=0)
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title(plot_title);

flood_map.plot(ax=ax, facecolor='deepskyblue', label="Flood Map Extent", alpha=0)
ctx.add_basemap(ax, crs=flood_map.crs, source=ctx.providers.OpenStreetMap.Mapnik)
plt.savefig("temp/flood_map_area_no_flood.png")
plt.show()

# Plot Flood Extent
# Reset Plot Title
plot_title = plot_title + " Flood Extent Map"
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title(plot_title);

flood_map.plot(ax=ax, facecolor='deepskyblue', label="Flood Map Extent")
ctx.add_basemap(ax, crs=flood_map.crs, source=ctx.providers.OpenStreetMap.Mapnik)
plt.savefig("temp/flood_map_area.png")
plt.show()

# Plot Flood Extent with Agriculture
fig, ax = plt.subplots(figsize=(12, 12))

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title(plot_title);

flood_map.plot(ax=ax, facecolor='deepskyblue', label="Flood Map Extent")
clipped_ag.plot(ax=ax, facecolor='lawngreen', label="Agriculture Flood", markersize=14)
ctx.add_basemap(ax, crs=flood_map.crs, source=ctx.providers.OpenStreetMap.Mapnik)
ax.legend(bbox_to_anchor=(1.0, .5), prop={'size': 18})
plt.savefig("temp/ag_flood.png")
plt.show()

# Plot Flood Extent with Population
fig, ax = plt.subplots(figsize=(12, 12))

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title(plot_title);

flood_map.plot(ax=ax, facecolor='deepskyblue', label="Flood Map Extent")
clipped_pop.plot(ax=ax, facecolor='yellow', label="Population Flood", markersize=14)
ctx.add_basemap(ax, crs=flood_map.crs, source=ctx.providers.OpenStreetMap.Mapnik)
ax.legend(bbox_to_anchor=(1.0, .5), prop={'size': 18})
plt.savefig("temp/pop_flood.png")
plt.show()

# Plot Flood Extent with OSM
fig, ax = plt.subplots(figsize=(12, 12))

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title(plot_title);

flood_map.plot(ax=ax, facecolor='deepskyblue', label="Flood Map Extent")
osm_cl_df.plot(ax=ax, facecolor='red', label="OSM Flood", markersize=14)
ctx.add_basemap(ax, crs=flood_map.crs, source=ctx.providers.OpenStreetMap.Mapnik)
ax.legend(bbox_to_anchor=(1.0, .5), prop={'size': 18})
plt.savefig("temp/osm_flood.png")
plt.show()

# Plot Flood Extent with Agriculture, Population, and OSM

fig, ax = plt.subplots(figsize=(12, 12))

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title(plot_title);

flood_map.plot(ax=ax, facecolor='deepskyblue', label="Flood Map Extent")
clipped_ag.plot(ax=ax, facecolor='lawngreen', label="Agriculture Flood", markersize=14)
clipped_pop.plot(ax=ax, facecolor='yellow', label="Population Flood", markersize=14)
osm_cl_df.plot(ax=ax, facecolor='red', label="OSM Flood", markersize=14)
ctx.add_basemap(ax, crs=flood_map.crs, source=ctx.providers.OpenStreetMap.Mapnik)
ax.legend(bbox_to_anchor=(1.0, .5), prop={'size': 18})
plt.savefig("temp/all_flood.png")
plt.show()'''

#####################################################################################################
print(f"\nThe amenity group table is:\n{amen_gp_ct}")

print(f"\nThe amenity group table is:\n{amen_ct}")

print(f"\nThe total number of agriculture in the flood extent is:\n{hectares} hectares")

print(f"\nThe total number of people in the flood extent is:\n{pop_count}")

# You can print out the test under here if you want but it's not necessary
'''
print(f"\nThe flood map GeoJSON file text is as follows:\n{fld_json}")

print(f"\nThe osm point GeoJSON file text is as follows:\n{osm_json}")

print(f"\nThe ag point GeoJSON file text is as follows:\n{ag_json}")

print(f"\nThe pop point GeoJSON file text is as follows:\n{pop_json}")

print(f"\nThe runtime for the script was:\n{datetime.datetime.now() - begin_time}")'''
