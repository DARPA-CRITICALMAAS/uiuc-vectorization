
import os
import logging
from rasterio.features import shapes, sieve 
from shapely.geometry import shape
import geopandas as gpd

log = logging.getLogger('DARPA_CMASS')

def polygonize(img, crs, transform, noise_threshold=10):
    # Remove "noise" from image by removing pixel groups below a threshold
    sieve_img = sieve(img, noise_threshold, connectivity=4)

    # Convert raster to vector shapes
    logging.debug('Converting to vector')
    shape_gen = shapes(sieve_img, connectivity=4, transform=transform)

    # Only use Filled pixels (1s) for shapes 
    geometries = [shape(geometry) for geometry, value in shape_gen if value == 1]

    return gpd.GeoDataFrame(geometry=geometries, crs=crs)

def exportVectorData(geoDataFrame, filename, layer=None, filetype='geopackage'):
    SUPPORTED_FILETYPES = ['json', 'geojson','geopackage']

    if filetype not in SUPPORTED_FILETYPES:
        log.error(f'ERROR : Cannot export data to unsupported filetype "{filetype}". Supported formats are {SUPPORTED_FILETYPES}')
        return # Could raise exception but just skipping for now.
    
    # GeoJson
    if filetype in ['json', 'geojson']:
        if os.path.splitext(filename)[1] not in ['.json','.geojson']:
            filename += '.geojson'
        geoDataFrame.to_crs('EPSG:4326')
        geoDataFrame.to_file(filename, driver='GeoJSON')

    # GeoPackage
    elif filetype == 'geopackage':
        if os.path.splitext(filename)[1] != '.gpkg':
            filename += '.gpkg'
        geoDataFrame.to_file(filename, layer=layer, driver="GPKG")