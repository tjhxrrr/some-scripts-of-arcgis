#-*- encoding:UTF-8 -*-
import arcpy
from arcpy.sa import *

# 更新地类编号DLBM
def update_dlbm(table):
    sumfield = ["DLBM"] 
    with arcpy.da.UpdateCursor(table, sumfield) as cursor:
        for row in cursor:
            row[0]=row[0][0:2]
            cursor.updateRow(row)

# 将计算所得值写入结果表
def dbftor(myresult, table, mystr, myfield):
    cursor_u=arcpy.UpdateCursor(myresult)
    cursor_s=arcpy.SearchCursor(table)
    for row in cursor_u:
        if row.getValue("CODE") == mycode:
            for rowchild in cursor_s:
                row.setValue(rowchild.getValue("Area"))
                cursor_u.updateRow(row)
            break   

# 将行政区面积写入结果表
def county_area(myresult,myboundary):
    cursor_u = arcpy.UpdateCursor(myresult)    
    for row in cursor_u:
        code = row.getValue("CODE")
        whereclause = "{0}='{1}'".format("CODE",code)
        cursor_b = arcpy.da.SearchCursor(myboundary,["CODE","Area"],whereclause)
        if cursor_b != None:
           for row_b in cursor_b:
               #print(row_b[1])
               row.setValue("Area_sum",float(row_b[1]))
               cursor_u.updateRow(row)

# 在结果表计算面积比例
def perc_cal(myresult,classes):
    for i in classes:
        area_field = "a" + i
        perc_field = "areaperc" + i
        cal_clause = "!" + area_field + "! / !Area_sum!"
        arcpy.CalculateField_management(myresult, perc_field,cal_clause , "PYTHON_9.3")


if __name__ == "__main__":

  arcpy.env.workspace = arcpy.GetParameterAsText(0)
  outWorkspace = arcpy.GetParameterAsText(0)
  arcpy.gp.overwriteOutput=1
  mydata = arcpy.GetParameterAsText(1)
  myboundary = arcpy.GetParameterAsText(2)
  myresult = arcpy.GetParameterAsText(3)
  inValueRaster = arcpy.GetParameterAsText(4)
  splitField = "CODE"
  zoneField = "DLBM"
  
  # liu
  arcpy.AddField_management(myboundary, "Area", "DOUBLE")
  arcpy.CalculateField_management(myboundary, "Area", "!shape.area@SQUAREKILOMETERS!", "PYTHON_9.3")
  arcpy.AddField_management(myresult,"Area_sum","DOUBLE")
  


  # 按照 myboundary 中的 splitField 字段对 mydata 进行 split
  arcpy.Split_analysis(mydata, myboundary, splitField, outWorkspace)
  # 添加结果字段（添加之后勿重复执行代码）
  classes = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '20']
  for i in classes:
    arcpy.AddField_management(myresult,"s"+i,"DOUBLE")
  for i in classes:
    arcpy.AddField_management(myresult,"a"+i,"DOUBLE")
  for i in classes:
    arcpy.AddField_management(myresult,"areaperc"+i,"DOUBLE")

  # 设置循环对象
  datasets = list(set(arcpy.ListFeatureClasses("*shp*"))-set(arcpy.ListFeatureClasses("*DLTB*"))-set(arcpy.ListFeatureClasses("*boundry*")))

  # 循环计算灯光指数和面积           
  for element in datasets:
      update_dlbm(element)
      mycode = element[:-4]
      myzonal = "s"+mycode+'.dbf'

      # 统计灯光   
      outZonalStatistics = ZonalStatisticsAsTable(element, zoneField, inValueRaster, myzonal, "DATA", "SUM")    
      myfield = u"SUM"
      mystr = u"s"
      dbftor(myresult, myzonal, mystr, myfield)

      # 计算面积
      myarea = "a"+mycode+'.dbf'
      arcpy.AddField_management(element, "Area", "DOUBLE")
      arcpy.CalculateField_management(element, "Area", "!shape.area@SQUAREKILOMETERS!", "PYTHON_9.3")
      arcpy.Statistics_analysis(element, myarea, [["Area", "SUM"]], "DLBM")       
      myfield = u"SUM_Area"
      mystr = u"a"
      dbftor(myresult, myarea, mystr, myfield)
  
  
  county_area(myresult,myboundary)
  perc_cal(myresult,classes)





