#!/usr/bin/env python3
#import matplotlib.pyplot as plt
print('start....')
import geopandas as gpd
import pandas as pd
import numpy as np
from osgeo import ogr
import rasterio
import joblib, time
from rasterio import features
import os
## Learn
time0=time.time()
def converCodeAndRasterize(huc_id):
    time1 = time.time()
    # below converCode of the nwi polygons
    #print('processing: ', huc_id)
    
    nwi_fn = 'NWI_HUC12_NAD83Albers_Intersect_class_ID_{0}.shp'.format(huc_id)       
    
    if os.path.exists(nwi_fn):
        try:
            ################ below is for empty
            df100All = gpd.read_file(nwi_fn)

            if df100All.empty:
                print('this huc_id is empty:  ', huc_id)
                #time1=time.time()
                # read in the nlcd file
                rst_fn = 'la_ccap1m_2017_masked_proYear_huc_{0}_150pixels.img'.format(huc_id)
                rst = rasterio.open(rst_fn)
                Arr = rst.read(1)
                out_arr = Arr *0 +0 # this is the out band
                meta = rst.meta.copy()
                meta.update(compress='lzw',dtype='uint8', nodata=255)

                out_fn = 'NWI_raster_ID_ccap1m_{0}.tif'.format(huc_id)
            
                with rasterio.open(out_fn, 'w+', **meta) as out:
                    #out_arr = out.read(1)
                    #out_arr.fill(0)
                    out.write_band(1, out_arr)

                #time2=time.time()
                #print('time to rasterize: ', (time2-time1)/60.0, ' minutes of id: ',huc_id )



            ###################### below is for not empty
            
            else:
                
                # read in the nlcd file
                rst_fn = 'la_ccap1m_2017_masked_proYear_huc_{0}_150pixels.img'.format(huc_id)
                rst = rasterio.open(rst_fn)
                meta = rst.meta.copy()
                meta.update(compress='lzw',dtype='uint8', nodata=255)

                out_fn = 'NWI_raster_ID_ccap1m_{0}.tif'.format(huc_id)

            
                with rasterio.open(out_fn, 'w+', **meta) as out:
                    out_arr = out.read(1)
                    out_arr.fill(0)

                    # this is where we create a generator of geom, value pairs to use in rasterizing
                    shapes = ((geom,value) for geom, value in zip(df100All.geometry, df100All.Class))

                    burned = features.rasterize(shapes=shapes, out=out_arr, transform=out.transform)
                    out.write_band(1, burned)

                time2=time.time()
                print('time to rasterize: ', (time2-time1)/60.0, ' minutes of id: ',huc_id )
            
        except Exception as oops:
            print('\nCan not be open, Problem ID: ', huc_id)
            print(oops)
    # below is for the ones with no nwi records
    else:
        print('this do not exist: ', huc_id)
        time1=time.time()
        # read in the nlcd file
        rst_fn ='la_ccap1m_2017_masked_proYear_huc_{0}_150pixels.img'.format(huc_id)
        rst = rasterio.open(rst_fn)
        Arr = rst.read(1)
        out_arr = Arr *0 +0 # this is the out band, assume all regions are highland
        meta = rst.meta.copy()
        meta.update(compress='lzw',dtype='uint8', nodata=255)

        out_fn = 'NWI_raster_ID_ccap1m_{0}.tif'.format(huc_id)

    
        with rasterio.open(out_fn, 'w+', **meta) as out:
            #out_arr = out.read(1)
            #out_arr.fill(0)
            out.write_band(1, out_arr)

        time2=time.time()
        #print('time to rasterize: ', (time2-time1)/60.0, ' minutes of id: ',huc_id )


if __name__ == "__main__":
    markToOcean_fn = 'CONUS_Watersheds_HUC12_NAD83Albers_markToOcean.shp'
    df_markToOcean =  gpd.read_file(markToOcean_fn)
    df_markToOcean_Only=df_markToOcean[df_markToOcean.la1m==2]
    df_markToOcean_Only=df_markToOcean_Only[df_markToOcean_Only.ToOcean==0]
    huc12List = np.unique(df_markToOcean_Only.HUC12_ID)
    huc12List.sort()
    numEle = len(huc12List)
    print('number of files of coastal region: ', numEle)

    joblib.Parallel(n_jobs=40)(joblib.delayed(converCodeAndRasterize)(huc_id) for huc_id in huc12List) # range(1,83335)


    ####71883,73### take a much longer time than others




time3=time.time()
print('time to finish whole script: ', (time3-time0)/60.0 )