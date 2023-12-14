import os
import json
import logging
import argparse
from tqdm import tqdm
import geopandas as gpd

import rasterio
from rasterio.features import shapes, sieve 
from shapely.geometry import shape, mapping

logging.basicConfig(level='INFO')

def parse_command_line():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('raster')
    parser.add_argument('-t', '--export_type',
                        choices=['geojson', 'geopackage'],
                        default='geopackage',
                        help='The file type to export the data to. (default: %(default)s)')
    parser.add_argument('-o', '--output',
                        default=None,
                        help='The location to write to')
    parser.add_argument('-d', '--threshold', default=10, help='Threshold in pixels of raster polygons to be removed')
    return parser.parse_args()

def main():
    # Get command line args
    args = parse_command_line()

    if not args.output:
        if os.path.isdir(args.raster):
            args.output = args.raster + '_out'
        else:
            args.output = os.path.splitext(args.raster)[0] + '.geojson'
    else: 
        if not os.path.exists(args.output) and not os.path.splitext(args.output)[1]:
            os.makedirs(args.output)

    # Get list of filepaths if directory
    if os.path.isdir(args.raster):
        rasters = [os.path.join(args.raster, f) for f in os.listdir(args.raster) if f.endswith('tif')]
    else:
        rasters = [args.raster]

    pbar = tqdm(rasters)
    for file in pbar:
        pbar.set_description(f'Processing {os.path.basename(file)}')
        pbar.refresh()
        basename = os.path.basename(os.path.splitext(file)[0])
        
        # Load data
        logging.debug(f'Loading {file}')
        with rasterio.open(file) as fh:
            img = fh.read(1)
            crs = fh.crs
            transform = fh.transform

        # Remove "noise" from image by removing pixel groups below a threshold
        sieve_img = sieve(img, args.threshold, connectivity=4)

        # Convert raster to vector shapes
        logging.debug('Converting to vector')
        shape_gen = shapes(sieve_img, connectivity=4, transform=transform)

        # Only use Filled pixels (1s) for shapes 
        geometries = [shape(geometry) for geometry, value in shape_gen if value == 1]

        data = gpd.GeoDataFrame( geometry=geometries, crs=crs)

        # Save Data
        if os.path.isdir(args.output):
            export_filename = os.path.join(args.output, basename)
        else:
            export_filename = args.output

        logging.info(f'Saving data to {export_filename}.')
        # GeoJson
        if args.export_type == 'geojson':
            if os.path.splitext(export_filename)[1] not in ['.json','.geojson']:
                export_filename += '.json'
            data.to_crs('EPSG:4326')
            data.to_file(export_filename, driver='GeoJSON')
        # GeoPackage
        elif args.export_type == 'geopackage':
            if os.path.splitext(export_filename)[1] != '.gpkg':
                export_filename += '.gpkg'
            data.to_file(export_filename, layer='cities', driver="GPKG")
        # How did we get here?
        else:
            print(f'Invalid export_type : \"{args.export_type}\"')


if __name__ == '__main__':
    main()