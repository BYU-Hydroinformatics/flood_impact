#!/usr/bin/env python
# coding: utf-8
#####################################################################################################

# All file paths for the datasets are examples that were used directly from Evan's local computer
# The file paths will need to be changed because the filepath locations of datasets per person will be different
# The datasets will be from OpenStreetMap, Croplands, and WorldPop, as well as the flood maps used
# Any file path that is called later should be referring to the 'temp' directory that will be created
#   and will not need to be changed

#####################################################################################################

# Load All Libraries/Modules
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

#####################################################################################################
# Set absolute path of working directory
#   If all of the datasets are in the same directory/folder, then you can use a shortened path when calling the files
path = "/Users/evan/flood_map_py/"

# Using the operating system (os) module we create a filepath shortcut
os.chdir(path)
print("Current Working Directory ", os.getcwd())

#####################################################################################################
# Load up croplands raster dataset path (either shortened as so or absolute)
croplands_path = "Peru/croplands_S10W80.tif"

# Load up population raster dataset path (either shortened as so or absolute)
pop_path = "Peru/worldpop_peru.tif"

# Load up the OpenSteetMap point shapefile dataset path (either shortened as so or absolute)
osm_file = "Peru/Chazuta_points.shp"

# Upload the flood map shapefile dataset path (either shortened as so or absolute)
# This requires that the flood map be a vector shapefile or a geojson
# If the flood map is in raster form, then use ras2poly function from the fldimpact_def.py before going much further
# If your flood map is a part of a GeoDatabase, use module fiona
#  Example code can be found in flood_impact_extraCodeSnippets.py
flood_file = "Peru/Chazuta_HAND_10m.shp"

#####################################################################################################

# This creates a variable called 'newpath' that is meant to be a temporary directory
# This directory will be used to store all temporary created files before we execute the script
newpath = path + 'temp'
if not os.path.exists(newpath):
    os.makedirs(newpath)

# This will delete all files in the temporary directory if it already exists
# If it cannot delete a file, it will print a code for you to see what file is troublesome
for filename in os.listdir(newpath):
    file_path = os.path.join(newpath, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))

# This is if you would like to visually inspect the geoprocessing outcomes by plotting the data
# Setting consistent plotting style throughout script
sns.set_style("dark")
sns.set(font_scale=1.5)
plot_title = "This Is The Plot Title"
begin_time = datetime.datetime.now()

#####################################################################################################
##### Can insert geodatabase extra code snippet here if needed #####

# Load shapefile to a GeoPandas Database
flood_map = gpd.read_file(flood_file)

# Gather the Coordinate Reference System (CRS) of the flood map
new_crs = flood_map.crs

#####################################################################################################

# ### Force the CRS to be the same for all datasets to reduce geoprocessing errors ( in this case ESPG:4236)

# Since the OSM, Croplands, and WorldPop datasets are in ESPG: 4326,
#   we will force the floood map shapefile to be same projection if it is not already the same
if flood_map.crs == "EPSG:4326":
    pass
else:
    # Change the Coordinate Reference System to epsg=4326
    data = flood_map.to_crs(epsg=4326)

    # Write new crs shapefile to the temp folder
    data.to_file('temp/fld_poly.shp')

    # Load new crs shapefile to a GeoPandas Dataframe and gather the new crs
    flood_map = gpd.read_file('temp/fld_poly.shp')
    new_crs = flood_map.crs

# If you want to save the shapefile polygon to a geojson file, go to flood_impact_extraCodeSnippet.py

#####################################################################################################
##### Croplands Raster Data #####


# Display raster data in Rasterio with flood map on same plot.

# Define future clipped raster file path
crop_clip = "temp/crop_clipped.tif"

# Clip raster data to the extent of the flood map
ras2shp_extent(croplands_path, flood_map, crop_clip)

# Define future reclassified raster file path
reclass_file = "temp/crop_reclass.tif"

# Leave only the cell value 2 and make all others the value of 0 in raster
# Croplands cell value of 2 is cultivated agriculture. All other cells are either water or other land
reclass_raster(crop_clip, reclass_file, 2, 2, 2, 0)

# Define future null raster file path
null_file = "temp/crop_null.tif"

# Make null all cells with raster cell value of 0 leaving only cell value of 2, which is all cultivated agriculture
ras_Null(reclass_file, null_file, 0)

# Convert Raster to Point Data
# Load data using georasters module (as 'gr')
data = gr.from_file(null_file)

# Convert data to Pandas DataFrame (DF)
single_df = data.to_pandas()

# Drop some columns in Pandas DF that are unnecessary
columns = ['row', 'col', 'value']
single_df = pd.DataFrame(single_df.drop(columns=columns))

# Create new column called 'Hectares' and make it the value respective to the resolution
# 1 hectare is 10,000 m^2. The resolution of this croplands dataset is 30-meters
# If the resolution is different for the agriculture data used, change the 30 to the new resolution below
single_df["Hectares"] = (30 ** 2)/10000
single_df = single_df[['x', 'y', 'Hectares']]  # organize columns


# Sequence to make Raster to Point Shapefile

# Define future crop point shapefile path
crop_pts = "temp/crop_pts.shp"

# Write as CVS file
single_df.to_csv(str(crop_pts.partition('.')[0] + '.csv'), index=None, header=True)

# Convert Pandas DF to Geopandas DF
single_df_point = gpd.GeoDataFrame(
    single_df, geometry=gpd.points_from_xy(single_df.x, single_df.y))

# Define Projection as the 'new_crs' previously called out
single_df_point.crs = {'init': new_crs}

# Writes as point shapefile
single_df_point.to_file(crop_pts)
cpts = gpd.read_file(crop_pts)

# Intersect the cropland points with the flood map
clipped_ag = gpd.clip(cpts, flood_map)

# Sum up total hectares of agriculture in flooded area
hectares = clipped_ag['Hectares'].sum()

#####################################################################################################
##### Population Raster Dataset #####
# This will be similar to the croplands dataset process. We just want the total population within the inundation area.
# This raster dataset from WorldPop contains raster cell values of the population in 100-meter resolution
# There are raster cells that have a NoData value. If this is not the case for you, then null those cells values

# Define future clipped raster file path
pop_clip = "temp/pop_clipped.tif"

# Clip raster data to the extent of the flood map
ras2shp_extent(pop_path, flood_map, pop_clip)

# Converting raster to point datafile
# Load data using georasters module (as 'gr')
data = gr.from_file(pop_clip)

# Convert to Pandas DF
pop_df = data.to_pandas()

# Drop some columns we do not want
columns =['row','col']
pop_df = pd.DataFrame(pop_df.drop(columns=columns))

# rename column named 'value' to 'Population' for easier interpretation
pop_df.rename(columns = {'value':'Population'}, inplace = True)
pop_df = pop_df[['x','y','Population']] # organize columns

# convert value type from float to an integer (this will truncate the value rather than round the value conventionally
pop_df = pop_df.astype({'Population': int})

# Define future population point shapefile path
pop_pts = "temp/pop_pts.shp"

# Write as CVS file
pop_df.to_csv(str(pop_pts.partition('.')[0] + '.csv'), index=None, header=True)

# Convert Pandas DF to Geopandas DF
pop_df_point = gpd.GeoDataFrame(
    pop_df, geometry=gpd.points_from_xy(pop_df.x, pop_df.y))

# Define Projection as the 'new_crs' previously called out
pop_df_point.crs = new_crs

# Writes as point shape file
pop_df_point.to_file(pop_pts)

popct = gpd.read_file(pop_pts)

# Intersect the points with the flood map
clipped_pop = gpd.clip(popct, flood_map)

# Sum up total population of agriculture in flooded area
pop_count = clipped_pop['Population'].sum().astype(int)

#####################################################################################################
##### OpenStreetMap Shapefile Dataset #####
# Amenities are the infrastructure that we care about from the OpenStreetMap data
# Amenities can be placed in a greater Amenity group (e.g., Amenity = 'school'; Amenity Group = 'education')

# Load up point shapefile of Infrastructure data to GeoPandas DF
osm_pts = gpd.read_file(osm_file)

# Intersect the points with the flood map
osm_cl_df = gpd.clip(osm_pts, flood_map)

# It is possible that the dataframe is empty so this is a conditional argument to combat that
if osm_cl_df.empty:
    # The amenity count
    amen_ct = 0

    # The amenity group count
    amen_gp_ct = 0
else:
    # Use a regular expression to extract what the amenity is from the column named 'other_tags'
    # Store the amenity is a new column called Amenity
    osm_cl_df['Amenity'] = osm_cl_df['other_tags'].str.extract('"amenity"=>"(.+?)"').astype(str)

    # Drop the columns we do not need
    columns = ['osm_id', 'name', 'barrier', 'highway', 'ref', 'address', 'is_in', 'place', 'man_made', 'other_tags']
    osm_cl_df = gpd.GeoDataFrame(osm_cl_df.drop(columns=columns))

    # Delete rows that are of value 'nan' in Amenity column
    osm_cl_df = osm_cl_df[osm_cl_df.Amenity != 'nan']

    # Create a new column for the amenity group and apply the amen_group function fom fldimpact_def.py
    # This function is specific to OSM data
    osm_cl_df["Amenity_Group"] = osm_cl_df.apply(lambda row: amen_group(row.Amenity), axis=1)

    # This converts the dataframe to a geodataframe and therefore can be plotted if desired
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
# Print off the different values for the flood impact metrics
print(f"\nThe amenity group table is:\n{amen_gp_ct}")

print(f"\nThe amenity group table is:\n{amen_ct}")

print(f"\nThe total number of agriculture in the flood extent is:\n{hectares} hectares")

print(f"\nThe total number of people in the flood extent is:\n{pop_count}")

# You can print out the runtime if you want to see if you want but it is not necessary
'''print(f"\nThe runtime for the script was:\n{datetime.datetime.now() - begin_time}")'''
