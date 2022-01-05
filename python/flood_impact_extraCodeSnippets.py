#####################################################################################################

# All file paths for the datasets are examples that were used directly from Evan's local computer
# The file paths will need to be changed because the filepath locations of datasets per person will be different
# The datasets will be from OpenStreetMap, Croplands, and WorldPop, as well as the flood maps used
# Any file path that is called later should be referring to the 'temp' directory that will be created
#   and will not need to be changed

#####################################################################################################


#########################
#  Extra Code Snippets  #
#########################

# These are extra things that may help depending on the situation


#######################
#  GeoDataBase Fiona  #
#######################

# This is to get flood extent map shapefile from a geodatabase
# for reading a geodatabase for shapefiles like from ArcGIS Pro
floodmap_gdb = "Chazuta_test.gdb"
layer = fiona.listlayers(floodmap_gdb)
print(layer)

layer_file = input("Type the layer from the printed list that reflects your flood map:\t")

# This will extract the flood map layer and upload it to a GeoPandas Dataframe and gathers the CRS
for layer in layer:
    flood_map = gpd.read_file(floodmap_gdb, layer = layer_file)
new_crs = flood_map.crs



################################
#  Saving Shapefile to GeoJSON #
################################

# Save the shapefile to a geojson
geojson_path = 'temp/flood_map.geojson'
flood_map.to_file(geojson_path, driver='GeoJSON')

# If you want to open the geojson file to use in a script, then use this
f = open('temp/fld_poly_test.geojson',)
fld_json = json.load(f)



############################
#  Plotting Data to a Map  #
############################

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
# Alter Plot Title
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
plt.show()