"""
This module aims to automatically download DMV AV crash reports from the website.
Download chromedriver into the current foler is a must.
"""

import requests
from selenium import webdriver
__author__ = "Mengqiao Yu"
__email__ = 'mengqiao.yu@berkeley.edu'


def get_url(root_url):

    # Change to your own path, put the driver into this folder.
    driver = webdriver.Chrome('/Users/MengqiaoYu/Desktop/GSR_18fall/DOT_pub/chromedriver')
    driver.get(root_url)

    #Extract the crash report download urls in 2018.
    urls_2018 = []
    names_2018 = []
    for i in range(12, 86 + 1):

        ele = driver.find_element_by_xpath('//*[@id="app_content"]/p[' + str(i) + ']/a')
        url = ele.get_attribute('href')
        name = ele.text.split(',')[0]

        urls_2018.append(url)
        names_2018.append(''.join(name.split()))

    driver.close()
    return urls_2018, names_2018

def download_url(urls, names, save_dir):

    for i, url in enumerate(urls):
        print("\tNow downloading file for %s..." %names[i])
        response = requests.get(url)

        with open(save_dir + names[i] + '.pdf', 'wb') as fd:
            fd.write(response.content)

def main():
    dmv_crash_url ='https://www.dmv.ca.gov/portal/dmv/detail/vr/autonomous/autonomousveh_ol316+'
    print("Start extracting all crash reports urls in 2018...")
    crash_urls, file_names = get_url(dmv_crash_url)
    print("\tThere are %d files in total." %len(crash_urls))

    download_dir = '/Users/MengqiaoYu/Desktop/GSR_18fall/DOT_pub/DMV_crash_reports/'
    print("Start downloading all files into folder %s." %download_dir)
    download_url(crash_urls, file_names, download_dir)

    print('---------------------THE END----------------------')

if __name__ == "__main__":
    main()
