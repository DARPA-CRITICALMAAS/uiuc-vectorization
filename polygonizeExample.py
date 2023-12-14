import os
import logging
import argparse
from tqdm import tqdm

import rasterio
from src.polygonize import polygonize, exportVectorData

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

        data = polygonize(img, crs, transform, args.threshold)

        # Save Data
        if os.path.isdir(args.output):
            export_filename = os.path.join(args.output, basename)
        else:
            export_filename = args.output

        exportVectorData(data, export_filename, args.export_type)

if __name__ == '__main__':
    main()