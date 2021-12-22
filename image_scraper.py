from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.keys import Keys
import requests
import io
from PIL import Image
import time
import os 
import argparse


def folder_name(output_dir):
    '''
    Cheks if last folder in output_dir exists, if not, creates it.
    Splits output_dir based on / and returns last position if / was not on last index, or second to last position if / was on last index
    The return is the f_name we used for files + count in img_from_google function 
    '''
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    f_name = str(output_dir).split('/')
    if f_name[-1]=='':
        return f_name[-2]
    else:
        return f_name[-1]
    

def formatted_query(query):  
    '''
    Used to format sys.arg so the google search showed appropriate blackspacing - NOT USED after argparse
    '''
    formatted = " "
    return formatted.join(query)


def scroll_down(wd, delay):
    '''
    Js script to scroll down to avoid reaching window limit
    '''
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);") # allows for execution of javascript commands
    time.sleep(delay)


def img_from_google(wd, delay, max_images, query, output_dir, f_name):
    '''
    Process:
        Google images shows them as thumbnails so we want to click on an image and utilize the popped up(enlarged) version's src link,
        otherwise we'll end up using downsampled or lower resolution versions of the actual image. 

        Inspect the images and grab the common or shared class name within the HTML tags.

        (edge case) Depending on the amount of images needing to be scraped, we need a way to scroll down on the search results, otherwise the program will stop at
        the last image since no more are being loaded in.
    '''

    wd.get("https://www.google.com/")
    search = wd.find_element_by_name('q')
    search.send_keys(query, Keys.ENTER)

    elem = wd.find_element_by_link_text('圖片') or wd.find_element_by_link_text('Images')
    elem.get_attribute('href')
    elem.click()
    
    image_urls = set()  # store urls so there's no duplicates

    while len(image_urls) < max_images: # keep scrolling down while we havent reached desired amount of images
        scroll_down(wd, delay)

        thumbnails = wd.find_elements(By.CLASS_NAME,"Q4LuWd")  #find elements on page with class name specifed, in this case Q4LuWd is thumbnails

        for count,img in enumerate(thumbnails[len(image_urls): max_images]): # iterate from last position in image_urls (new images)
            try:
                img.click()  # click on the images
                time.sleep(delay) # give it time to let the new image pop up occur
            except:
                continue
            
            images = wd.find_elements(By.CLASS_NAME, "n3VNCb")  # look for real image in popped up window using its CLASS tag
            for image in images: # iterate through images and return a valid image, could potentially return multiple
                if image.get_attribute('src') and 'http' in image.get_attribute('src'): # if image has a src attribut and that attribute has http in it, its valid
                    image_urls.add(image.get_attribute('src'))
                    print("Found image: {}".format(image.get_attribute('src')))
                    download_img(output_dir, image.get_attribute('src'), f_name+'_'+str(count)+'.png')


def download_img(download_path, url, file_name):
    '''
    http request for url.content(image) which is converted and stores in binary inside of memory then 
    converted to PIL image for easy saving using image.save()

    try/except in case it fails
    '''

    try:   # try / except in case download fails, it continues with rest of code
        image_content = requests.get(url).content  # allows Http request to the url // url.content -> image
        image_file = io.BytesIO(image_content) # convert and store image in bytes.io dtype -> store directly inside of memory
        image = Image.open(image_file)  # convert binary data to PIL image to easily alow us to save using PIL image.save
        file_path = download_path + file_name

        with open(file_path, "wb") as f: # open filepath in write bytes mode
            image.save(f, "PNG")
        
        print("Done")
    except Exception as e:
        print("Failed -{}".format(e))


### Selenium automates the browser but need a browser to automate, so download web driver for any browser ###
dir = os.path.dirname(os.path.realpath('_file__'))
PATH = os.path.join(dir, 'chromedriver')
wd = webdriver.Chrome(PATH)

parser = argparse.ArgumentParser(description='Scrape images from google image')
parser.add_argument('--query', action='store', required=True, type=str, help='search query')
parser.add_argument('--output', default=os.getcwd(),help='output directory')
parser.add_argument('--delay', default=1, help='Delay in seconds for actions requiring delay')
parser.add_argument('--max_images', default=1, help='Number of images to download')
args = parser.parse_args()

#output_dir, query = args.output, args.query
#f_name = folder_name(args.output)

img_from_google(wd, int(args.delay), int(args.max_images), args.query, args.output, folder_name(args.output))  # downloads images
wd.quit()
