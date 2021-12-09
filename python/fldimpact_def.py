# This will be the script with all of the different definitions used for the flood impact process

#######################
#  Import Libraries  #
#######################

from osgeo import ogr, gdal
import rasterio as rio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np
from shapely.geometry import box
import json

# May use in def ras2shp_extent
import fiona
from fiona.crs import from_epsg


#######################
#  Utility Functions  #
#######################


# This will organize the different amenities into a group
def amen_group(string):
    # input arrays here for the different amenities
    food = ['bar', 'biergarten', 'cafe', 'drinking_water', 'fast_food',
            'food_court', 'ice_cream', 'pub', 'restaurant']

    education = ['college', 'driving_school', 'kindergarten', 'language_school',
                 'library', 'toy_library', 'music_school', 'school', 'university']

    transportation = ['bicycle_parking', 'bicycle_repair_station', 'bicycle_rental',
                      'boat_rental', 'boat_sharing', 'bus_station', 'car_rental',
                      'car_sharing', 'car_wash', 'vehicle_inspection', 'charging_station',
                      'ferry_terminal', 'fuel', 'grit_bin', 'motorcycle_parking',
                      'parking', 'parking_entrance', 'parking_space', 'taxi', 'kick-scooter_rental']

    financial = ['atm', 'bank', 'bureau_de_change']

    healthcare = ['baby_hatch', 'clinic', 'dentist', 'doctors', 'hospital', 'nursing_home',
                  'pharmacy', 'social_facility', 'veterinary']

    entertainment = ['arts_centre', 'brothel', 'casino', 'cinema', 'community_centre',
                     'conference_centre', 'events_venue', 'fountain', 'gambling',
                     'love_hotel', 'nightclub', 'planetarium', 'public_bookcase',
                     'social_centre', 'stripclub', 'studio', 'swingerclub', 'theatre']

    others = ['animal_boarding', 'animal_breeding', 'animal_shelter', 'baking_oven',
              'childcare', 'clock', 'crematorium', 'dive_centre',
              'funeral_hall', 'grave_yard', 'gym', 'hunting_stand',
              'internet_cafe', 'kitchen', 'kneipp_water_cure', 'lounger', 'marketplace',
              'monastery', 'photo_booth', 'place_of_mourning', 'place_of_worship', 'public_bath',
              'public_building', 'refugee_site', 'vending_machine', 'user defined']

    public_service = ['courthouse', 'embassy', 'fire_station', 'police', 'post_box', 'post_depot',
                      'post_office', 'prison', 'ranger_station', 'townhall']

    facilities = ['bbq', 'bench', 'dog_toilet', 'give_box', 'shelter', 'shower', 'telephone',
                  'toilets', 'water_point', 'watering_place']

    waste_man = ['sanitary_dump_station', 'recycling', 'waste_basket', 'waste_disposal',
                 'waste_transfer_station']

    # go through the different functions
    # which should return the right thing
    for x in food:
        if x.__contains__(string):
            return 'food'

    for x in education:
        if x.__contains__(string):
            return 'education'

    for x in transportation:
        if x.__contains__(string):
            return 'transportation'

    for x in financial:
        if x.__contains__(string):
            return 'financial'

    for x in healthcare:
        if x.__contains__(string):
            return 'healthcare'

    for x in entertainment:
        if x.__contains__(string):
            return 'entertainment'

    for x in others:
        if x.__contains__(string):
            return 'others'

    for x in public_service:
        if x.__contains__(string):
            return 'public_service'

    for x in facilities:
        if x.__contains__(string):
            return 'facilities'

    for x in waste_man:
        if x.__contains__(string):
            return 'waste_management'


# Need to get coordinates of the geometry in JSON format for Rasterio.
# Use this definition.
def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


# This is to use clip a raster to the extent of the flood map shapefile
# that is assumed to be at the extent the user wants.
# It is also assumed that the input_shapefile already had gpd.read_file(input_shapefile) executed
def ras2shp_extent(input_rasterfile, input_shapefile, output_rasterfile):
    # open raster file using rio
    crop = rio.open(input_rasterfile)

    # Gather the extent of the flood map
    bounds = input_shapefile.total_bounds

    # Get shapefile Coordinate Reference System (crs)
    fld_crs = str(input_shapefile.crs)

    # Load extent into bounding box
    bbox = box(bounds[-4], bounds[-3], bounds[-2], bounds[-1])

    # Create a GeoDataFrame from the bounding box
    # geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=fld_crs)

    # Project the Polygon into same CRS as the grid
    geo = geo.to_crs(crs=crop.crs)

    # Get the geometry coordinates by using the function above
    coords = getFeatures(geo)

    # Clip the raster with the polygon
    out_img, out_transform = mask(dataset=crop, shapes=coords, crop=True)

    # Copy the metadata
    out_meta = crop.meta.copy()

    # Define the new projection as the same as the flood map
    # floodmap_crs = str(flood_map.crs)
    new_crs = {'init': fld_crs}

    # update metadata
    out_meta.update({"driver": "GTiff",
                     "height": out_img.shape[1],
                     "width": out_img.shape[2],
                     "transform": out_transform,
                     "crs": new_crs}
                    )

    # Save the clipped raster to disk
    out_tif = output_rasterfile

    with rio.open(out_tif, "w", **out_meta) as dest:
        dest.write(out_img)

    # Close raster file
    crop.close()


# This takes a single band raster and reclassifies it into two different values.
# input_file is the filepath (e.g. "/Users/Documents/input_file.tif")
# output_file is the filepath (e.g. "/Users/Documents/output_file.tif")
# arg1 and val1 work as such: raster values >= arg1 will become val1
# optional_arg2 and optional_val2 is performed after the first argument and value and work as such:
#           # raster values < optional_arg2 will become optional_val2. The default's are 0 and 0
def reclass_raster(input_file, out_file, arg1, val1, optional_arg2=0, optional_val2=0):
    # load various gdal input
    driver = gdal.GetDriverByName('GTiff')
    file = gdal.Open(input_file)
    band = file.GetRasterBand(1)
    clist = band.ReadAsArray()

    # reclassify everything to 0 that is not cell value 2 (meaning agriculture)
    clist = np.where(clist >= arg1, val1, clist)
    clist = np.where(clist < optional_arg2, optional_val2, clist)

    # create new file
    file2 = driver.Create(out_file, file.RasterXSize, file.RasterYSize, 1)
    file2.GetRasterBand(1).WriteArray(clist)

    # spatial ref system
    proj = file.GetProjection()
    georef = file.GetGeoTransform()
    file2.SetProjection(proj)
    file2.SetGeoTransform(georef)
    file2.FlushCache()
    del file2


# This takes a single band raster and converts all raster cell values of 0 to be noData
def ras_Null(input_file, output_file, null_value):
    ds = gdal.Open(input_file)
    ds = gdal.Translate(output_file, ds, noData=null_value)
    ds = None


# This takes a single band raster and converts it to a polygon shapefile.
# This makes all noData values to be 0
# To rectify this, open the output_file as a geopandas dataframe and delete all rows with Value of 0.
# We then save the dataframe back to the output_file shapefile
def ras2poly(input_file, output_file, nan_value):
    # read raster in rasterio to get crs
    crs = str(rio.open(input_file).crs)

    # read in raster using gdal
    raster = gdal.Open(input_file)

    # get raster band
    band = raster.GetRasterBand(1)

    # set gdal options
    drv = ogr.GetDriverByName('ESRI Shapefile')
    outfile = drv.CreateDataSource(output_file)
    outlayer = outfile.CreateLayer('polygonized raster', srs=None)
    newField = ogr.FieldDefn('Value', ogr.OFTReal)
    outlayer.CreateField(newField)

    # use gdal raster to polygon procedure
    gdal.Polygonize(band, None, outlayer, 0, [])
    outfile = None

    # load as a geopandas dataframe
    fld_map = gpd.read_file(output_file)

    # Delete rows that are of value 'nan' in Amenity column
    fld_map = fld_map[fld_map.Value != nan_value]

    # Make flood map .shp in same projection as the flood map .tif
    fld_map.crs = {'init': crs}

    # Writes as point shape file
    fld_map.to_file(output_file)


# Using Shapely to see if the new shapefile .is_valid. If it is not the buffer by (0) to fix the geometry
def fix_geometries(input_file):
    # Read in the .shp file as a geopandas dataframe
    fld_map = gpd.read_file(input_file)

    # Iterate through the rows to see if it is valid
    for invalid_row in fld_map[~fld_map.is_valid].iterrows():
        # where invalid_row[0] is the index in flood_maps of the invalid row
        # invalid_row[1] is the row from the flood_maps geodataframe
        fld_map.loc[invalid_row[0], 'geometry'] = invalid_row[1].geometry.buffer(0)

    # Load up the fixed geometry of the .shp file to the same file
    fld_map.to_file(input_file)