#!/usr/bin/env python3
#import modules
print('start...')
import glob
import time,os,sys
import subprocess
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import *
startTime = time.time()
gdal.AllRegister()
# create parameter arrays
def mosaic(infns,outfn):
    rowsL,colsL,minXL,maxXL,minYL,maxYL,pixelWL,pixelHL = [],[],[],[],[],[],[],[]
    nums = len(infns)
    print ('number of files: ',nums)
    for numi in range(nums):
        inDSi = gdal.Open(infns[numi],GA_ReadOnly)
        if inDSi is None:
            print (infns[numi],'could not be open')
            sys.exit(1)
        rowsL.append((inDSi.RasterYSize)-300)
        colsL.append((inDSi.RasterXSize)-300)
        transform = inDSi.GetGeoTransform()
        minXL.append(transform[0]+150)
        maxYL.append(transform[3]-150)
        pixelWL.append(transform[1])
        pixelHL.append(transform[5])
        maxXL.append(minXL[numi]+(colsL[numi]*pixelWL[numi]))        
        minYL.append(maxYL[numi]+(rowsL[numi]*pixelHL[numi]))
    # get the boundary of the output file
    minXB = min(minXL)-200
    maxXB = max(maxXL)+200
    minYB = min(minYL)-200
    maxYB = max(maxYL)+200
    #print 'minXL,maxXL,minYL,maxYL: ',minXL,maxXL,minYL,maxYL
    # compute the rows and cols of the output file
    colss = int(round((maxXB-minXB)/pixelWL[0]))
    rowss = int(round((maxYB-minYB)/abs(pixelHL[0])))
    outArr = np.zeros((rowss,colss),dtype=np.uint8) # background value is 0
    print('rowss: ', rowss, 'colss: ', colss)
    # create the output image
    dataType = inDSi.GetRasterBand(1).DataType
    driver = gdal.GetDriverByName('HFA')
    outDS = driver.Create(outfn,colss,rowss,1,dataType)
    outBand = outDS.GetRasterBand(1)

    print ('rowsL: ',rowsL,'colsL: ',colsL)
    # start write the output image
    for numi in range(nums):
        xOffset = int(round((minXL[numi]-minXB)/pixelWL[0]))
        yOffset = int(round((maxYL[numi]-maxYB)/pixelHL[0]))
        filenamei = infns[numi]
        nameid = filenamei.split("_")[-2]
        inccapfn = 'la_ccap1m_2017_masked_proYear_huc_{0}_150pixels.img'.format(nameid)
        inDSccapi = gdal.Open(inccapfn,GA_ReadOnly)
        print('inDSccapi rows and cols: ', inDSccapi.RasterYSize, inDSccapi.RasterXSize)
        if inDSccapi is None:
            print (inccapfn, 'could not be open')
            sys.exit(1)
        inArrccap = inDSccapi.GetRasterBand(1).ReadAsArray(150,150,colsL[numi],rowsL[numi])

        inDSi = gdal.Open(filenamei,GA_ReadOnly)
        #print 'numi,xOffset,yOffset: ',numi,xOffset,yOffset
        if inDSi is None:
            print (infns[numi], 'could not be open')
            sys.exit(1)
        inArr = inDSi.GetRasterBand(1).ReadAsArray(150,150,colsL[numi],rowsL[numi])
        #inArr[inArrccap==100]=255
        xxID,yyID = np.where((inArr!=0)&(inArr!=10)&(inArr!=255)&(inArrccap!=0)&(inArrccap!=255))
        inArrSel = inArr[xxID,yyID]
        xxIDPlus = xxID+yOffset
        yyIDPlus = yyID+xOffset
        outArr[xxIDPlus,yyIDPlus]=inArrSel
        #print 'inArray cols: ',colsL[numi],'inArray rows: ',rowsL[numi]

    ct = gdal.ColorTable()
    # Some examples
    '''
    ct.SetColorEntry( 0, (178,178,178, 255) )
    ct.SetColorEntry( 1, (190,255,232, 255) )
    ct.SetColorEntry( 2, (0,112,255, 255) )
    ct.SetColorEntry( 3, (233,255,190, 255) )
    ct.SetColorEntry( 4, (115,255,223, 255) )
    ct.SetColorEntry( 5, (38,115,0, 255) )
    ct.SetColorEntry( 52, (168,0,0, 255) )
    ct.SetColorEntry( 55, (255,127,127, 255) )
    ct.SetColorEntry( 56, (163,255,115, 255) )
    ct.SetColorEntry( 6, (76,230,0, 255) )
    ct.SetColorEntry( 120, (255,190,190, 255) )
    ct.SetColorEntry( 121, (0,38,115, 255) )
    ct.SetColorEntry( 136, (255,211,127, 255) )
    ct.SetColorEntry( 148, (255,170,0, 255) )
    ct.SetColorEntry( 221, (115,178,255, 255) )
    '''

    ct.SetColorEntry( 0, (178,178,178, 255) )
    ct.SetColorEntry( 1, (190,255,232, 255) )
    ct.SetColorEntry( 2, (255,235,190, 255) )
    ct.SetColorEntry( 3, (255,235,190, 255) )
    ct.SetColorEntry( 4, (255,235,190, 255) )
    ct.SetColorEntry( 5, (255,235,190, 255) )
    ct.SetColorEntry( 52, (168,0,0, 255) )
    ct.SetColorEntry( 6, (190,255,232, 255) )
    ct.SetColorEntry( 121, (0,38,115, 255) )
    ct.SetColorEntry( 221, (115,178,255, 255) )


    # Set the color table for your band
    outBand.SetColorTable(ct)

    outBand.WriteArray(outArr,0,0)
    # calculate statistics
    outBand.FlushCache()
    outBand.GetStatistics(0,1)
    outBand.SetNoDataValue(255)
    # georeferencing the output image
    geotransform = (minXB,pixelWL[0],0,maxYB,0,pixelHL[0])
    outDS.SetGeoTransform(geotransform)
    # set the projection
    proj = inDSi.GetProjection()
    outDS.SetProjection(proj)

    # close the datasource
    inDSi = None
    outDS = None
###########################################################################################


### Below is for RasterChange Shrink 1Loss 2Gain Pixels ###########################
infns = glob.glob('rasterChange_1m_150pixels_ID_*_onlyCertain.tif')


#infns = infn[0:2]
#infns = infn1+infn2
#infns = infns[100:101]
print('number of files: ', len(infns))
#print('old number: ', len(infn), ' new number: ', len(infn_markOcean))

outfn = 'rasterChange_1m_onlyCertain_mosaic_conus_buffer200m_background0.img'
### Above is for RasterChange Shrink 1Loss 2Gain Pixels ###########################
results = mosaic(infns,outfn)
#p.apply_async(mosaic,args=(infns,outfn))

endTime = time.time()
print ('file mosaic takes '+ str((endTime - startTime)/60.0)+' minutes')
