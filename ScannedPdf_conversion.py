from PIL import Image as PI
import sys
from os import listdir
import pyocr
import pyocr.builders
import codecs
from wand.image import Image
import io
import numpy as np
import scipy
from scipy import signal
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt


DEBUG = False

def extract_checkmark(filename):
    """
    using file 'GM_Cruise_06032018'
    :return: a standard check mark representation
    :rtype: numpy.ndarray
    """
    print(f"Extract check mark from file: {filename}")
    ck_pdf = Image(filename=filename+'.pdf', resolution=300)
    ck_jpeg = ck_pdf.convert('jpeg')
    ck_lastpage = ck_jpeg.sequence[-1]
    npimg_ck = np.array(PI.open(io.BytesIO(Image(image=ck_lastpage).make_blob('jpeg'))))
    ck = npimg_ck[325:375,815:865]

    return ck

def extract_pages(filename):
    img_pdf = Image(filename=filename, resolution=300)
    img_jpeg = img_pdf.convert('jpeg')
    img_thirdpage =  img_jpeg.sequence[-1]
    img_secondpage = img_jpeg.sequence[-2]

    return img_secondpage, img_thirdpage

def find_loc(img_thirdpage, checkmark):
    """
    find the locations of check marks in the third page
    """
    # [400:2500,1575:1825]
    npimg_thirdpage = np.array(PI.open(io.BytesIO(Image(image=img_thirdpage).make_blob('jpeg'))))
    npimg_thirdpage_col2 = npimg_thirdpage[300:2600,1575:1925]
    # import pdb; pdb.set_trace()
    plt.imshow(npimg_thirdpage_col2)
    col_2 = scipy.signal.convolve(
        np.int32(npimg_thirdpage_col2.mean(-1)),
        255-checkmark.mean(-1).astype(np.uint32),mode='valid')
    col_2 =col_2 / col_2.max() * 255

    if DEBUG:
        fig_result = plt.figure()
        plt.imshow(np.uint8(np.logical_and(1, col_2<160)), cmap='gray')
        plt.show()
        plt.savefig('result.jpg')
        import pdb; pdb.set_trace()

    cm_pixel_row = np.where(col_2 < 160)[0] // 75
    cm_pixel_col = np.where(col_2 < 160)[1] // 126
    cm_row, cm_row_count = np.unique(cm_pixel_row, return_counts=True)
    print("row:", cm_row)
    print("row_count:", cm_row_count)
    cm_row = cm_row[np.where(cm_row_count >= 100)]
    cm_col = []
    for r in cm_row:
        c = cm_pixel_col[np.where(cm_pixel_row == r)]
        c, cc = np.unique(c, return_counts=True)
        c = c[np.argmax(cc)]
        cm_col.append(c)
    cm_col = np.array(cm_col)
    print("row", cm_row)
    print("col", cm_col)

    if DEBUG:
        plt.figure()
        plt.imshow(npimg_thirdpage_col2)
        plt.show()

    # loc_eff = loc[0][np.where(loc[1] >= 100)]
    # loc_2 = np.unique(np.where(col_2 < 160)[1]//126, return_counts=True)
    # loc_eff_2 = loc_2[0][np.where(loc_2[1] >= 100)]
    # assert len(loc_eff) == len(loc_eff_2), "Not same number of check marks!"
    # print("locations are:")
    # print(loc_eff)
    # print(loc_eff_2)
    return cm_row, cm_col

def extract_words(img_secondpage):
    # Image to text
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        print("NO OCR tool found")
        sys.exit(1)
    tool = tools[0]
    # print("Will use toll '%s'." % (tool.get_name()))

    langs = tool.get_available_languages()
    # print("Available languages: %s" % ", ".join(langs))
    lang = langs[0]
    # print("Will use lang '%s'." % (lang))
    print("Performing OCR on page 2.")
    width, height = img_secondpage.size
    left, top, right, bottom = 0, height/5*3, width, height/10*9
    txt = tool.image_to_string(
        PI.open(
            io.BytesIO(
                Image(image=img_secondpage).make_blob('jpeg'))).crop((left, top, right, bottom)),
        lang = lang,
        builder = pyocr.builders.TextBuilder()
    )

    # word_boxes = tool.image_to_string(
    #     Image.open('Waymo_082018_Page_1.png'),
    #     lang="eng",
    #     builder=pyocr.builders.WordBoxBuilder()
    # )
    # for word_box in word_boxes:
    #     print(word_box.content)
    with open('test.txt', 'w') as f:
        f.write(txt)
        f.write("\n\n\n")
    # with codecs.open('page1_test1.txt', 'w') as file_descriptor:
    #     builder.write_file(file_descriptor, txt)

def main():
    # Column 1 contains weather, lighting, roadway surface, and roadway condition
    COL_1= ["Clear", "Cloudy", "Raining", "Snowing", "Fog/Visibility", "Other", "Wind",
            "",
            "Daylight", "Dusk-Dawn", "Dark-Street Lights", "Dark-No Street Lights",
            "",
            "Dry", "Wet", "Snowy-Icy", "Slippery(Muddy, Oily)",
            "",
            "Holes, Deep Rut", "Loose Material", "Construction", "Reduced Roadway Width",
            "Flooded", "Other", "No unusual Conditions"]
    COL_2 = ["STOPPED", "PROCEEDING STRAIGHT", "RAN OFF ROAD", "MAKING RIGHT TURN",
             "MAKING LEFT TURN", "MAKING U TURN", "BACKING", "SLOWING/STOPPING",
             "PASSING OTHER VEHICLE", "CHANGING LANES", "PARKING MANUEVER",
             "ENTERING TRAFFIC", "OTHER UNSAFE TURNING", "XING INTO OPPOSING LANE",
             "PARKED", "MERGING", "TRAVELING WRONG WAY", "OTHER", "TYPE OF COLLISION",
             "HEAD-ON", "SIDE SWIPE", "REAR END", "BROADSIDE", "HIT OBJECT",
             "OVERTURNED", "VEHICLE/PEDESTRIAN", "OTHER"]
    VEH = ["veh1(AV)","veh2(CV)"]
    ck_image = extract_checkmark(filename='GM_Cruise_06032018')
    reports_dir = 'DMV_reports'

    for f in listdir(reports_dir):
        print(f"Reading file: {f}")
        second_page, third_page = extract_pages(filename=f)
        loc_row, loc_col = find_loc(img_thirdpage=third_page, checkmark=ck_image)
        result = {}
        loc_col_u = np.unique(loc_col)
        for c in loc_col_u:
            attrs = [COL_2[_] for _ in loc_row[np.where(loc_col == c)]]
            result[VEH[c]] = '/'.join(attrs)
        print(result)

        extract_words(img_secondpage=second_page)

if __name__ == "__main__":
    main()





### Extract info from the last page
# plt.ion()
# import pdb;pdb.set_trace()
# Filter 1
# ccc= scipy.signal.convolve(np.int32(npimg_lastpage[325:2500,1575:1825].mean(-1)),ck.mean(-1).astype(np.uint32),mode='valid');plt.imshow(ccc/ccc.max(),cmap='gray')
# Filter 2 (better, use this one)
# plt.imshow(ccc1/ccc1.max(),cmap='gray')


### Installation
# in the command line: brew install tesseract
# tesseract -v (check if succefully installed)
# pip install pyocr


