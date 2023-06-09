import os
import json
import shutil
import mysql.connector

vals=[('UAT28_S_176_0_1962_2119_197_499', 'M8+X1'), \
('UAT28_S_176_10_2037_8957_323_426', 'M8+X1'), \
('UAT28_S_176_11_2009_9576_120_348', 'M8+X1'), \
('UAT28_S_176_12_5386_10088_618_769', 'M8+X1'), \
('UAT28_S_176_13_2007_10205_170_468', 'M8+X1'), \
('UAT28_S_176_14_1816_11428_119_400', 'M8+X1'), \
('UAT28_S_176_15_2165_11442_211_384', 'M8+X1'), \
('UAT28_S_176_16_2473_11450_192_335', 'M8+X1'), \
('UAT28_S_176_1_1947_2771_323_458', 'M8+X1'), \
('UAT28_S_176_2_1987_3990_163_277', 'M8+X1'), \
('UAT28_S_176_3_1996_4596_175_335', 'M8+X1'), \
('UAT28_S_176_4_1979_5228_191_359', 'M8+X1'), \
('UAT28_S_176_5_5219_5267_238_281', 'M8+X1+N5'), \
('UAT28_S_176_6_1989_5830_135_317', 'M8+X1'), \
('UAT28_S_176_7_2000_7094_349_557', 'M8+X1'), \
('UAT28_S_176_8_1918_8333_233_539', 'M8+X1'), \
('UAT28_S_176_9_2589_8339_629_517', 'M8+X1+N5'), \
('UAT28_S_222_0_2963_1381_301_379', 'N35+G1+N35'), \
('UAT28_S_222_10_1965_3882_146_228', 'N35+G1'), \
('UAT28_S_222_11_2250_4457_259_385', 'N35+G1+N35'), \
('UAT28_S_222_12_5196_4488_230_391', 'N35+G1'), \
('UAT28_S_222_13_1855_4463_239_328', 'N35+G1'), \
('UAT28_S_222_14_4580_4460_192_254', 'N35+G1'), \
('UAT28_S_222_15_4870_4466_191_299', 'N35+G1'), \
('UAT28_S_222_16_5802_5099_203_286', 'N35+G1+N35'), \
('UAT28_S_222_17_2939_5122_171_270', 'N35+G1+N35'), \
('UAT28_S_222_18_1940_5127_165_203', 'N35+G1'), \
('UAT28_S_222_19_4625_5702_311_317', 'N35+G1'), \
('UAT28_S_222_1_2008_1370_242_297', 'N35+G1'), \
('UAT28_S_222_20_5048_5706_166_294', 'N35+G1+N35'), \
('UAT28_S_222_21_1850_5688_224_211', 'N35+G1'), \
('UAT28_S_222_22_2257_5728_203_280', 'N35+G1'), \
('UAT28_S_222_23_1868_6951_320_339', 'N35+G1'), \
('UAT28_S_222_24_2286_6956_232_329', 'N35+G1'), \
('UAT28_S_222_25_1852_7569_340_452', 'N35+G1'), \
('UAT28_S_222_26_4948_7567_292_438', 'N35+G1'), \
('UAT28_S_222_27_5302_7562_242_364', 'N35+G1'), \
('UAT28_S_222_28_4537_7587_261_457', 'N35+G1'), \
('UAT28_S_222_29_2372_7634_290_228', 'N35+G1'), \
('UAT28_S_222_2_2972_1995_282_230', 'N35+G1+N35'), \
('UAT28_S_222_30_4657_8200_224_482', 'N35+G1'), \
('UAT28_S_222_31_1835_8189_234_373', 'N35+G1'), \
('UAT28_S_222_32_2169_8228_222_267', 'N35+G1'), \
('UAT28_S_222_33_1863_8780_237_375', 'N35+G1'), \
('UAT28_S_222_34_2182_8860_232_286', 'N35+G1'), \
('UAT28_S_222_35_4639_8814_98_280', 'N35+G1'), \
('UAT28_S_222_36_1953_9427_272_343', 'N35+G1'), \
('UAT28_S_222_37_4678_9465_275_362', 'N35+G1'), \
('UAT28_S_222_38_7568_9456_81_195', 'N35+G1'), \
('UAT28_S_222_39_1959_10048_244_332', 'N35+G1'), \
('UAT28_S_222_3_7585_2600_426_567', 'N35+G1'), \
('UAT28_S_222_40_4673_10081_265_349', 'N35+G1'), \
('UAT28_S_222_41_1856_11277_207_301', 'N35+G1'), \
('UAT28_S_222_42_4667_11297_205_318', 'N35+G1'), \
('UAT28_S_222_43_2255_11331_220_306', 'N35+G1'), \
('UAT28_S_222_4_2941_2615_316_326', 'N35+G1+N35'), \
('UAT28_S_222_5_4711_3214_247_480', 'N35+G1'), \
('UAT28_S_222_6_2187_3233_378_405', 'N35+G1'), \
('UAT28_S_222_7_1796_3219_330_476', 'N35+G1'), \
('UAT28_S_222_8_2543_3246_191_221', 'N35+G1'), \
('UAT28_S_222_9_2919_3899_172_288', 'N35+G1+N35'), \
('UAT28_S_241_0_2864_1415_384_215', 'N37+N35+N35+N35'), \
('UAT28_S_241_10_6257_4484_547_275', 'N37+N35+N35+N35'), \
('UAT28_S_241_11_2929_4483_500_183', 'N37+N35+N35+N35'), \
('UAT28_S_241_12_7554_5088_482_288', 'N37+N35+N35+N35'), \
('UAT28_S_241_13_1781_5129_340_174', 'N37+N35+N35+N35'), \
('UAT28_S_241_14_2920_5128_352_173', 'N37+N35+N35+N35'), \
('UAT28_S_241_15_7005_5125_320_145', 'N37+N35+N35+N35'), \
('UAT28_S_241_16_2875_5679_497_250', 'N37+N35+N35+N35'), \
('UAT28_S_241_17_1765_5747_391_169', 'N37+N35+N35+N35'), \
('UAT28_S_241_18_2819_6360_768_228', 'N37+N35+N35+N35'), \
('UAT28_S_241_19_5352_6945_407_196', 'N37+N35+N35+N35'), \
('UAT28_S_241_1_1859_2628_648_306', 'N37+N35+N35+N35'), \
('UAT28_S_241_20_7087_7587_693_286', 'N37+N35+N35+N35'), \
('UAT28_S_241_21_6181_7548_768_286', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_22_2316_7604_741_260', 'N37+N35+N35+N35'), \
('UAT28_S_241_23_3035_8207_819_447', 'N37+N35+N35+N35'), \
('UAT28_S_241_24_4911_8193_863_515', 'N37+N35+N35+N35'), \
('UAT28_S_241_25_5855_8244_910_584', 'N37+N35+N35+N35'), \
('UAT28_S_241_26_3945_8210_762_455', 'N37+N35+N35+N35'), \
('UAT28_S_241_27_7531_8836_441_196', 'N37+N35+N35+N35'), \
('UAT28_S_241_28_5475_9410_825_272', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_29_2889_9454_792_271', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_2_2871_2621_569_260', 'N37+N35+N35+N35'), \
('UAT28_S_241_30_1814_9465_655_225', 'N37+N35+N35+N35'), \
('UAT28_S_241_31_7069_10031_406_230', 'N37+N35+N35+N35'), \
('UAT28_S_241_32_2810_10053_556_248', 'N37+N35+N35+N35'), \
('UAT28_S_241_33_1782_10698_505_220', 'N37+N35+N35+N35'), \
('UAT28_S_241_34_6270_11289_822_449', 'N37+N35+N35+N35'), \
('UAT28_S_241_3_3669_2639_634_227', 'N37+N35+N35+N35'), \
('UAT28_S_241_4_6286_3255_477_249', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_5_3495_3276_614_233', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_6_5416_3283_572_221', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_7_7070_3281_542_173', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_8_2749_3304_471_150', 'N37+N35+N35+N35+N5'), \
('UAT28_S_241_9_1776_3867_524_255', 'N37+N35+N35+N35'), \
('UAT28_S_78_0_1795_1396_300_291', 'D46+X1+Ff100'), \
('UAT28_S_78_10_5760_6325_492_450', 'D46+X1+Z5'), \
('UAT28_S_78_11_6429_6324_567_440', 'D46+X1+Z5'), \
('UAT28_S_78_12_6165_7551_359_588', 'D46+X1+Z5'), \
('UAT28_S_78_13_2547_7565_364_327', 'D46+X1+Z5'), \
('UAT28_S_78_14_1797_8803_518_522', 'D46+X1+Z5'), \
('UAT28_S_78_15_7238_8933_1053_740', 'D46+X1+Z5'), \
('UAT28_S_78_16_7076_8793_331_322', 'D46+X1+Z5'), \
('UAT28_S_78_17_6368_8767_241_319', 'D46+X1+Z5'), \
('UAT28_S_78_18_3160_8798_218_364', 'D46+X1+Z5'), \
('UAT28_S_78_19_5974_8811_205_321', 'D46+X1+Z5'), \
('UAT28_S_78_1_5953_2550_388_333', 'D46+X1+Ff100'), \
('UAT28_S_78_20_1790_9456_376_328', 'D46+X1+Z5'), \
('UAT28_S_78_21_1776_10666_324_245', 'D46+X1+Z5+Ff100'), \
('UAT28_S_78_22_5013_11297_486_353', 'D46+X1+Ff100'), \
('UAT28_S_78_23_6222_11284_353_321', 'D46+X1+Z5'), \
('UAT28_S_78_24_4391_11311_441_355', 'D46+X1+Z5'), \
('UAT28_S_78_25_2617_11322_366_338', 'D46+X1+Z5'), \
('UAT28_S_78_26_3194_11344_497_342', 'D46+X1+Ff100'), \
('UAT28_S_78_2_6400_2537_253_242', 'D46+X1+Ff100'), \
('UAT28_S_78_3_5458_2570_272_305', 'D46+X1+Ff100'), \
('UAT28_S_78_4_7563_2559_317_279', 'D46+X1+Ff100'), \
('UAT28_S_78_5_7080_2578_295_299', 'D46+X1+Ff100'), \
('UAT28_S_78_6_3264_2603_290_254', 'D46+X1+Ff100'), \
('UAT28_S_78_7_7442_3254_568_677', 'D46+X1+Z5'), \
('UAT28_S_78_8_3285_3209_682_436', 'D46+X1+Z5'), \
('UAT28_S_78_9_1772_3242_300_379', 'D46+X1+Z5'), \
('UAT28_S_82_0_1947_1402_381_367', 'D52+X1'), \
('UAT28_S_82_1_1965_6991_489_379', 'D53'), \
('UAT28_S_82_2_2897_7481_692_737', 'D52+G17'), \
('UAT28_S_82_3_1904_7598_472_326', 'D53'), \
('UAT28_S_82_4_1963_10059_528_515', 'D53'), \
('UAT28_S_82_5_1942_11502_604_802', 'D53') ]



rootdir=r"c:\hieraproject"

#connect to database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="pTurin1880!",
  database="hiera"
)


def loadSqlToDict(sSql):
    d={}
    c=hieradb.cursor()
    c.execute(sSql)
    for x in c.fetchall():
        d[x[0]]=x[1]
    c.close()
    return d

def retrieveValuesFromDb(sSql):
    d={}
    c=hieradb.cursor()
    c.execute(sSql)
    x=c.fetchone()
    c.close()
    return x

sourceidFromCode=loadSqlToDict("SELECT name,id from hiera.sources")
metatypeidFromName=loadSqlToDict("SELECT name,id from hiera.metadatatypes")
nSourceIdWimmer=sourceidFromCode["Wimmer"]
for v in vals:
    graphemeid=retrieveValuesFromDb("SELECT id from graphemes where source_id="+str(nSourceIdWimmer)+" and name='" + v[0] + "'")[0]
    sql = "UPDATE graphemesmetadata SET value='"+v[1]+"' WHERE grapheme_id=" + str(graphemeid) + " AND metadatatype_id="+ str( metatypeidFromName['MDC'])
    c = hieradb.cursor()
    c.execute(sql)
    hieradb.commit()    
    print(sql)
