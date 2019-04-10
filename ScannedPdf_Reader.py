"""
This file aims to convert Scanned Pdf to txt file.
"""

__author__ = "Mengqiao Yu"
__email__ = "mengqiao.yu@berkeley.edu"

from PIL import Image as PI
import sys
from os import listdir
import pyocr
import pyocr.builders
from wand.image import Image
import io


def extract_pages(filename):
    img_pdf = Image(filename=filename, resolution=300)
    img_jpeg = img_pdf.convert('jpeg')
    print("Have convertd scanned pdf to jpeg.\n\n")
    return img_jpeg


def extract_words(imgs, save_dir, filename):
    """
    Use OCR to convert images to text file.
    Conversion quality is better than using acrobat own conversion tool.
    """
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        print("NO OCR tool found")
        sys.exit(1)
    tool = tools[0]
    print("Will use toll '%s'." % (tool.get_name()))

    langs = tool.get_available_languages()
    print("Available languages: %s" % ", ".join(langs))
    lang = langs[0]
    print("Will use lang '%s'." % (lang))

    for i, img in enumerate(imgs.sequence):
        # width, height = img.size
        print("Performing OCR on page %d." %i)
        try:
            txt = tool.image_to_string(
                PI.open(
                    io.BytesIO(
                        Image(image=img).make_blob('jpeg'))),
                lang = lang,
                builder = pyocr.builders.TextBuilder()
            )
            with open(save_dir + filename + '.txt', 'a') as f:
                f.write(txt)
                f.write("\n\n\n")
        except Exception:
            print("Error on page %d." %i)


def main():

    ### Change the directory of crash reports to your own dir!!!
    target_dir = 'download/'
    result_dir = 'result/'

    ### Apply conversion to all the files under this directory
    for f in listdir(hearings_dir):
        if f.startswith('.'):
            continue
        print(f"Reading file: {f}")

        images = extract_pages(filename=hearings_dir+f)
        extract_words(imgs=images, save_dir=result_dir, filename=f.split('.')[0])


if __name__ == "__main__":
    main()


