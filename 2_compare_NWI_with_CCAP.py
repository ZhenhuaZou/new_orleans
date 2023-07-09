#!/usr/bin/env python3
print('start...')
import os,sys
import numpy as np
from numpy import ma
from osgeo import gdal
from osgeo import ogr
import time, glob
#print (waffls.__version__)
import rasterio
import joblib
import geopandas as gpd
from scipy import ndimage


gdal.AllRegister()

def get_statistics(huc_id):
      nwi_fn = 'NWI_raster_ID_ccap1m_{0}.tif'.format(huc_id)
      nlcd_fn = 'la_ccap1m_2017_masked_proYear_huc_{0}_150pixels.img'.format(huc_id)
      huc_fn = 'CONUS_Watersheds_HUC12_NAD83Albers_markToOcean_{0}.shp'.format(huc_id)
    
      if os.path.exists(nwi_fn):

            try:
                  # read in the images
                  src = rasterio.open(nwi_fn)
                  nwiArr = src.read(1)
                  #nwiArr2 = src.read(2)
                  nlcdArr = rasterio.open(nlcd_fn).read(1)
                  ###### adjust shift #####
                  # wetland: 1, marine: 2, E1:3, L1:4, R:5, vegetated wetland: 6

                  # remove background values based on nlcd/ccap
                  validID = np.where((nlcdArr==255)|(nlcdArr==0)) # background value is 100, and 0
                  nwiArr[validID] = 255 # background value is 255
                  # number of valid pixels
                  totalHucPN = np.sum(nwiArr!=255)
                  totalWetPN = np.sum((nwiArr==1)|(nwiArr==6)) # nwi, 0: upland, 1: other wetland, 2: Marine, 3: E1, 4: L1, 5: R
                  totalHigPN = np.sum(nwiArr==0) # 

                  outArr = nwiArr + 0

                  # buffer the wetland
                  #ArrForH = ((nwiArr<1)|(nwiArr>7)).astype(np.uint8)
                  #distH = ndimage.distance_transform_edt(ArrForH) # distance from 0, expand 1
                  #ArrForH[np.where(distH <= 2)] = 0 # expand 2 pixel for gain assessment// the H is 0



                  # shrink for loss assessment
                  ArrForLossAss = ((nwiArr==1)|(nwiArr==6)).astype(np.uint8)
                  #dist = ndimage.distance_transform_edt(ArrForLossAss) # distance from 0, expand 1
                  #ArrForLossAss[np.where(dist <= 1)] = 0
                  

                  # shrink for gain assessment
                  ArrForGainAss = (nwiArr==0).astype(np.uint8)
                  #distG = ndimage.distance_transform_edt(ArrForGainAss) # distance from 0, expand 1
                  #ArrForGainAss[np.where(distG <= 1)] = 0 # shrank 1 pixel for gain assessment

                  #shrink for water assessment
                  ArrForWaterAss = (nwiArr==6).astype(np.uint8)
                  #distW = ndimage.distance_transform_edt(ArrForWaterAss) # distance from 0, expand 1
                  #ArrForWaterAss[np.where(distW <= 1)] = 0 # shrank 1 pixel for gain assessment
                  

                  

                  #nlcd_classes = [11, 12, 21, 22, 23, 24, 31, 41, 42, 43, 51, 52, 71, 72, 73, 74, 81, 82, 90, 95]
                  # 21: developed, open space 
                  # 22: developed, low intensity
                  # 23: developed, medium intensity
                  # 24: developed, high intensity
                  # 82: cultivated crops
                  # 11: open water

                  # 0 is highland, 1 is wetland, 2, 3, 4 are excluded for wetland loss, 5, 6, 7, 8 are excluded for wetland loss
                  ################# all nwi or nlcd area
                  allnwiWetPN = np.sum((nwiArr>0)&(nwiArr<10))
                  allnwiHigPN = np.sum(nwiArr==0)

                  allnlcdWetPN = np.sum(((nlcdArr>12)&(nlcdArr<20))|((nlcdArr>20)&(nlcdArr<25)))
                  allnlcdHigPn = totalHucPN - allnlcdWetPN

                  ################# loss assessment
                  # get the wetland region in nwi
                  totalWetSPN = np.sum(ArrForLossAss)
                  nwiWetID = (ArrForLossAss==1)
                  nlcdSelWet = nlcdArr[nwiWetID]
                  nwiArrSelWet = nwiArr[nwiWetID]
                  

                  nlcd52WetPN = np.sum(nlcdSelWet==2) # impervious high intensity
                  nlcd53WetPN = np.sum(nlcdSelWet==3) # impervious open space
                  nlcd54WetPN = np.sum(nlcdSelWet==4) # impervious open space
                  nlcd55WetPN = np.sum(nlcdSelWet==5) # impervious open space
                  nlcd56WetPN = np.sum(nlcdSelWet==6) # cultivated crops
                  nlcd120WetPN = np.sum(nlcdSelWet==20) # bare land
                  #nlcd221WetPN = np.sum((nlcdSelWet==21)&(nwiArrSelWet==6)) # open water
                  #nlcd58WetPN = np.sum(nlcdSelWet==8) # grassland


                  # reset outSelWet values
                  outSelWet = outArr[nwiWetID]
                  outSelWet[nlcdSelWet==2] = 52
                  #outSelWet[nlcdSelWet==3] = 53
                  #outSelWet[nlcdSelWet==4] = 54
                  #outSelWet[nlcdSelWet==5] = 55
                  #outSelWet[nlcdSelWet==6] = 56
                  #outSelWet[nlcdSelWet==20] = 120

                  # gain
                  #outSelWet[(nlcdSelWet==21)&(nwiArrSelWet==6)] = 221
                  #outSelWet[nlcdSelWet==8] = 58
                  
                  # put it back
                  outArr[nwiWetID] = outSelWet

                  ################# gain assessment
                  # get the highland (non wetland region) in nwi
                  totalHigSPN = np.sum(ArrForGainAss)
                  nwiHigID = (ArrForGainAss==1)
                  nlcdSelHig = nlcdArr[nwiHigID]
                  
                  nlcd121HigPN = np.sum(nlcdSelHig==21) # open water
                  #nlcd136HigPN = np.sum((nlcdSelHig==13)|(nlcdSelHig==16)) # forest wetland
                  #nlcd148HigPN = np.sum((nlcdSelHig==14)|(nlcdSelHig==15)|(nlcdSelHig==17)|(nlcdSelHig==18)) #scrub/shrub, emergent wetland
                  # reset outSelHig values
                  outSelHig = outArr[nwiHigID]
                  outSelHig[nlcdSelHig==21] = 121
                  #outSelHig[(nlcdSelHig==13)|(nlcdSelHig==16)] = 136
                  #outSelHig[(nlcdSelHig==14)|(nlcdSelHig==15)|(nlcdSelHig==17)|(nlcdSelHig==18)] = 148
                  # put it back
                  outArr[nwiHigID] = outSelHig

                  ################# water assessment
                  # get the highland (non wetland region) in nwi
                  totalVegSPN = np.sum(ArrForWaterAss)
                  nwiVegID = (ArrForWaterAss==1)
                  nlcdSelVeg = nlcdArr[nwiVegID]
                  
                  nlcd221VegPN = np.sum(nlcdSelVeg==21) # open water
                  
                  # reset outSelHig values
                  outSelVeg = outArr[nwiVegID]
                  outSelVeg[nlcdSelVeg==21] = 221
                  
                  # put it back
                  outArr[nwiVegID] = outSelVeg  #### change this line in the future

                  
                  ### output the change raster
                  nwi_out_fn = 'rasterChange_1m_150pixels_ID_{0}_onlyCertain.tif'.format(huc_id)

                  
                  meta = src.meta.copy()
                  meta.update(compress='lzw',dtype='uint8', nodata=255, count=1)
                  if os.path.exists(nwi_out_fn):
                        filenamesrm = glob.glob(nwi_out_fn[:-4]+'.*')
                        for i in filenamesrm:
                              os.remove(i)

                  with rasterio.open(nwi_out_fn, 'w', **meta) as dst:
                        dst.write(outArr.astype(rasterio.uint8), 1)
                        dst.write_colormap(
                              1,
                              {
                              0: (178,178,178, 255),
                              1: (190,255,232, 255),
                              2: (0,112,255, 255),
                              3: (233,255,190, 255),
                              4: (115,255,223, 255),
                              5: (38,115,0, 255),
                              52: (168,0,0, 255),
                              55: (255,127,127, 255),
                              56: (163,255,115, 255),
                              6: (76,230,0, 255),
                              120: (255,190,190, 255),
                              121: (0,38,115, 255),
                              136: (255,211,127, 255),
                              148: (255,170,0, 255),
                              221: (115,178,255, 255)
                              })

                  # output
                  df = gpd.read_file(huc_fn)
                  huc_area = df['geometry'].area
                  df['hucAreaG'] = huc_area/4046.86 # huc area in acre

                  #df['HucAreaP'] = totalHucPN * 900.0/4046.86
                  df['totnwiWet'] = allnwiWetPN * 1.0 /10000
                  df['totnwiUpl'] = allnwiHigPN * 1.0 /10000
                  df['totnlcdWet'] = allnlcdWetPN * 1.0 /10000
                  df['totnlcdUpl'] = allnlcdHigPn * 1.0 /10000

                  df['selnwiWet'] = totalWetPN * 1.0 /10000# exclue 1,2,3, 41, 42, 43
                  df['selnwiWetS'] = totalWetSPN * 1.0 /10000 # exclue 1,2,3, 41, 42, 43
                  df['wetTo52A'] = nlcd52WetPN * 1.0 /10000
                  df['wetTo52Ap'] = nlcd52WetPN * 1.0 *10000/huc_area
                  df['wetTo52P'] = nlcd52WetPN *100.0 /totalWetSPN

                  #df['wetTo53A'] = nlcd53WetPN * 100.0 /4046.86
                  #df['wetTo53Ap'] = nlcd53WetPN * 100.0 *10000/huc_area
                  #df['wetTo53P'] = nlcd53WetPN *100.0 /totalWetSPN

                  #df['wetTo54A'] = nlcd54WetPN * 100.0 /4046.86
                  #df['wetTo54Ap'] = nlcd54WetPN * 100.0 *10000/huc_area
                  #df['wetTo54P'] = nlcd54WetPN *100.0 /totalWetSPN

                  #df['wetTo55A'] = nlcd55WetPN * 100.0 /4046.86
                  #df['wetTo55Ap'] = nlcd55WetPN * 100.0 *10000/huc_area
                  #df['wetTo55P'] = nlcd55WetPN *100.0 /totalWetSPN

                  #df['wetTo56A'] = nlcd56WetPN * 100.0 /4046.86
                  #df['wetTo56Ap'] = nlcd56WetPN * 100.0 *10000/huc_area
                  #df['wetTo56P'] = nlcd56WetPN *100.0 /totalWetSPN

                  #df['wetTo58A'] = nlcd58WetPN * 100.0 /4046.86
                  #df['wetTo58Ap'] = nlcd58WetPN * 100.0 *10000/huc_area
                  #df['wetTo58P'] = nlcd58WetPN *100.0 /totalWetSPN

                  #df['wetTo523A'] = (nlcd52WetPN + nlcd53WetPN) * 100.0 /4046.86
                  #df['wetTo523Ap'] = (nlcd52WetPN + nlcd53WetPN) * 100.0 *10000/huc_area
                  #df['wetTo523P'] = (nlcd52WetPN + nlcd53WetPN) *100.0 /totalWetSPN

                  #df['wetTo120A'] = nlcd120WetPN * 100.0/4046.86
                  #df['wetTo120Ap'] = nlcd120WetPN * 100.0 *10000/huc_area
                  #df['wetTo120P'] = nlcd120WetPN *100.0 /totalWetSPN

                  df['wetTo221A'] = nlcd221VegPN * 1.0 /10000
                  df['wetTo221Ap'] = nlcd221VegPN * 1.0 *10000/huc_area
                  df['wetTo221P'] = nlcd221VegPN *100.0 /totalVegSPN

                  df['selnwiUpl'] = totalHigPN * 1.0 /10000 # only highland
                  df['selnwiUpS'] = totalHigSPN * 1.0 /10000 # only highland
                  df['uplTo121A'] = nlcd121HigPN * 1.0 /10000
                  df['uplTo121Ap'] = nlcd121HigPN * 1.0 *10000/huc_area
                  df['uplTo121P'] = nlcd121HigPN *100.0 /totalHigSPN

                  #df['uplTo136A'] = nlcd136HigPN * 100.0 /4046.86
                  #df['uplTo136Ap'] = nlcd136HigPN * 100.0 *10000/huc_area
                  #df['uplTo136P'] = nlcd136HigPN *100.0 /totalHigSPN

                  #df['uplTo148A'] = nlcd148HigPN * 100.0 /4046.86
                  #df['uplTo148Ap'] = nlcd148HigPN * 100.0 *10000/huc_area
                  #df['uplTo148P'] = nlcd148HigPN *100.0 /totalHigSPN

                  df['allWaterA'] = (nlcd121HigPN + nlcd221VegPN) * 1.0 /10000
                  df['allWaterAp'] = (nlcd121HigPN + nlcd221VegPN)  * 1.0 *10000/huc_area
                  df['allWaterP'] = (nlcd121HigPN + nlcd221VegPN)  *100.0 /(totalWetSPN+totalVegSPN)


                  df['allDiffA'] = (nlcd52WetPN + nlcd121HigPN + nlcd221VegPN) * 1.0 /10000
                  df['allDiffAp'] = (nlcd52WetPN + nlcd121HigPN + nlcd221VegPN)  * 1.0 *10000/huc_area
                  df['allDiffP'] = (nlcd52WetPN + nlcd121HigPN + nlcd221VegPN)  *100.0 /(totalWetSPN+totalHigSPN)

                  huc_out_fn = 'Huc12_{0}_change_statis_onlyCertain.shp'.format(huc_id)

                  driver = ogr.GetDriverByName('ESRI Shapefile')
                  if os.path.exists(huc_out_fn):
                        driver.DeleteDataSource(huc_out_fn)
                  df.to_file(huc_out_fn)
                  print('finish: ', huc_id)
                  print('.......................................................................................')
                  

            except Exception as oops:
                  print('\nProblem ID: ', huc_id)
                  print(oops)
# generate the input variables needed for the parallel processing
time0=time.time()
print('start time: ', time.ctime())
  
if __name__=='__main__':
      markToOcean_fn = 'CONUS_Watersheds_HUC12_NAD83Albers_markToOcean.shp'
      df_markToOcean =  gpd.read_file(markToOcean_fn)
      df_markToOcean_Only=df_markToOcean[df_markToOcean.la1m==2]

      huc12List = np.unique(df_markToOcean_Only.HUC12_ID)
      huc12List.sort()
      print('number of hucs: ', len(huc12List))
      print('huc12List[0]: ',huc12List[0] )
      joblib.Parallel(n_jobs=30)(joblib.delayed(get_statistics)(huc_id) for huc_id in huc12List)   #83335
      # 6: 0-20000
      

time1=time.time()
print('**************Finished in: '+ str((time1-time0)/60.0)+' minutes')  


    