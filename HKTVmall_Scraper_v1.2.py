from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from time import sleep, time
import csv
import os
from datetime import datetime
import pandas as pd
import sys
#import numpy as np
#import unidecode
import warnings
import re
import sys
warnings.filterwarnings('ignore')



def read_inputs():

    file = os.getcwd() + '\\links.csv'
    if not os.path.exists(file):
        print("Couldn't find the input file 'links.csv', exiting the program ...")
        sys.exit()

    try:
        df = pd.read_csv(file)
        df.drop_duplicates(inplace=True)
        links = df.iloc[:, 0].values.tolist()
    except:
        print("Error in processing the input file 'links.csv', exiting the program ...")
        sys.exit()

    return links

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    #chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--lang=en")
    chrome_options.add_argument('--headless=new')
    chrome_options.page_load_strategy = 'normal'
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver

def process_links(driver, processed_links, output):

    print('-'*100)
    print('Processing links before scraping')
    print('-'*100)
    # in case all the input links are already processed
    if False not in processed_links:
        df = pd.read_csv(output)
        df.drop_duplicates(inplace=True)
        prod_links = df['Link'].values.tolist()
        return prod_links

    for i, link in enumerate(links):
        # processed link
        if processed_links[i] == True: continue
        # single product link
        if 'search' not in link:
            with open(output, 'a', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow([link])
            continue
        driver.get(link)
        sleep(3)
        fail = 0

        while True:
            try:
                # checking if a category link is provided
                grid = wait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.productGrid")))
                try:
                    spans = wait(grid, 30).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.product-brief-wrapper")))
                    with open(output, 'a', newline='', encoding='utf-8-sig') as file:
                        for span in spans:
                            sub_link = wait(span, 30).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))[-1]
                            writer = csv.writer(file)
                            writer.writerow([sub_link.get_attribute("href")])
                    # end of pages
                    try:
                        button = wait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.next-btn.disable")))
                        break
                    except:
                        pass
                    # moving to the next page
                    try:
                        button = wait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.next-btn")))
                        driver.execute_script("arguments[0].click();", button)
                        #sleep(10)
                    except:
                        break

                except:
                    print(f"Warning: The site didn't load all the products under link {i+1}, restarting the bot ...")
                    print('-'*100)
                    driver.quit()
                    sleep(5)
                    driver = initialize_bot()
                    driver.get(link)
                    sleep(3)
            except:
                if 'search' not in link:
                    with open(output, 'a', newline='', encoding='utf-8-sig') as file:
                        writer = csv.writer(file)
                        writer.writerow([link])
                break

        # input link is processed
        processed_links[i] = True

    # return processed links
    df = pd.read_csv(output)
    df.drop_duplicates(inplace=True)
    prod_links = df['Link'].values.tolist()
    return prod_links


def scrape_prods(driver, prod_links, output1, output2):

    keys = ["Product ID",	"Product URL",	"Product Title",	"Product Price",	"Product Origin",	"Product Category",	"Product Description",	"Product Delivery",	"Product Rating",	"Product Image",	"Product Comments",	"Return Info",	"Store Name",	"Store Rating",	"Sold"]
    print('Scraping links')
    print('-'*100)
    # reading scraped links for skipping
    df = pd.read_csv(output1)
    output_links = df['Product URL'].values.tolist()
    nlinks = len(prod_links)
    for i, link in enumerate(prod_links):
        if link in output_links: continue
        prod = {}
        for key in keys:
            prod[key] = ''
        comm = []
        driver.get(link)
        sleep(1)

        # handling 404 error
        try:
            error = wait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//div[@class='pagenotfound text-center']")))
            raise
        except:
            pass

        try:
            # scraping product URL
            prod['Product URL'] = link

            # scraping product ID
            try:
                ID = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.searchKeyword"))).text.split(":")[-1]
                ID = re.sub("([^\x00-\x7F])+","",ID)
                prod['Product ID'] = ID.replace('&nbsp;', '')              
            except:
                pass

            # scraping product title
            try:
                title = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.breadcrumb-btm"))).text
                prod['Product Title'] = title
            except:
                pass
                
            # scraping product price
            try:
                price_div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.price")))
                price = wait(price_div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))[0].text.replace('$', '').strip()
                prod['Product Price'] = price
            except:
                pass

            # scraping product origion, description, delivery and return 
            try:
                details = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.productDetailPanelTable")))
                trs = wait(details, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
                for tr in trs:
                    try:
                        span = wait(tr, 1).until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))[0]
                    except:
                        continue
                    if 'Country of Origin' in span.text or '產地' in span.text:
                        origin = tr.text.replace('Country of Origin', '', 1).strip()
                        origin = origin.replace('產地', '', 1).strip()
                        prod['Product Origin'] = origin        
                    elif 'Description' in span.text or '商品簡介' in span.text:
                        des = tr.text.replace('Description', '', 1).strip()
                        des = des.replace('商品簡介', '', 1).strip()
                        prod['Product Description'] = des        
                    elif 'Delivery / Return' in span.text or '送貨/退貨' in span.text:
                        try:
                            lis = wait(tr, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))[:-1]
                            delivery = ''
                            for li in lis:
                                delivery += li.text + '\n' 
                            prod['Product Delivery'] = delivery
                            retrn = wait(tr, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))[-1].text
                            prod['Return Info'] = retrn
                        except:
                            deivery = tr.text.replace('Delivery / Return', '', 1).strip()
                            deivery = deivery.replace('送貨/退貨', '', 1).strip()
                            prod['Product Delivery'] = deivery
            except:
                pass

            # scraping product category
            try:
                cat_div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.relevant")))
                cat = wait(cat_div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))[0].text
                prod['Product Category'] = cat
            except:
                pass

            # scraping product rating
            try:
                rating = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.averageRating"))).text
                prod['Product Rating'] = rating
            except:
                pass

            # scraping product image link
            try:
                img_div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.productImageGallery")))
                img = wait(img_div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "img")))[0]
                url = img.get_attribute("data-primaryimagesrc")
                if url[:6].lower() == 'https:':
                    prod['Product Image'] = url
                else:
                    prod['Product Image'] = 'https:' + url
            except:
                pass

            # scraping product comments
            try:
                rev_div = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='reviewTab']")))
                revs = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.review-title")))
                rev = revs[0].text
                prod['Product Comments'] = rev
                for row in revs:
                    comm.append([ID, row.text])
            except:
                # No product reviews are available
                pass

            # scraping store name
            try:
                store_div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.store-panel")))
                store = wait(store_div, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.name"))).text
                prod['Store Name'] = store
            except:
                pass

            # scraping store rating
            try:
                store_div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.store-panel")))
                store_rating = wait(store_div, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.storeRatingValue"))).text
                prod['Store Rating'] = store_rating
            except:
                pass

            # scraping products sold
            try:
                sold = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.salesNumber-container"))).text.replace('Sold', '').strip()
                sold = re.sub("([^\x00-\x7F])+","",sold)
                prod['Sold'] = sold
            except:
                # No sold data is available
                pass

            # checking if the produc data has been scraped successfully
            if prod['Product ID'] != '' and prod['Product Title'] != '' and prod['Product Price'] != '':
                # output scraped data
                output_data(prod, comm, output1, output2)

                print(f'Link {i+1} of {nlinks} is scraped successfully!')
        except:
            print(f'Error in scraping link {i+1} of {nlinks}, skipping ...') 
            continue       


def output_data(prod, comm, output1, output2):

    row1 = [prod["Product ID"],	prod["Product URL"],	prod["Product Title"],	prod["Product Price"],	prod["Product Origin"],	prod["Product Category"],	prod["Product Description"],	prod["Product Delivery"],	prod["Product Rating"],	prod["Product Image"],	prod["Product Comments"],	prod["Return Info"],	prod["Store Name"],	prod["Store Rating"],	prod["Sold"]]


    with open(output1, 'a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(row1)    
    if len(comm) > 0:
        with open(output2, 'a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerows(comm)


def initialize_output():

    # removing the previous output file
    cols1 = ["Product ID",	"Product URL",	"Product Title",	"Product Price",	"Product Origin",	"Product Category",	"Product Description",	"Product Delivery",	"Product Rating",	"Product Image",	"Product Comments",	"Return Info",	"Store Name",	"Store Rating",	"Sold"]
    cols2 = ["Product ID",	"Product Comments"]

    stamp = datetime.now().strftime("%d_%m_%Y_%H_%M")
    path = os.getcwd() + '\\scraped_data\\' + stamp
    if os.path.exists(path):
        os.remove(path) 
    os.makedirs(path)

    file1 = f'HKTVmall_{stamp}.csv'
    file2 = f'HKTVmall_Comments_{stamp}.csv'
    file3 = "temp.csv"
    # Windws and Linux slashes
    if os.getcwd().find('/') != -1:
        output1 = path.replace('\\', '/') + "/" + file1
        output2 = path.replace('\\', '/') + "/" + file2
        output3 = path.replace('\\', '/') + "/" + file3
    else:
        output1 = path + "\\" + file1
        output2 = path + "\\" + file2
        output3 = path + "\\" + file3

    # writing files headers
    with open(output1, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(cols1)    
    with open(output2, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(cols2)    
    with open(output3, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Link'])

    return output1, output2, output3



if __name__ == '__main__':

    start = time()
    links = read_inputs()
    output1, output2, output3 = initialize_output()
    processed_links = [False]*len(links)
    while True:
        try:
            try:
                driver = initialize_bot()
            except Exception as err:
                print('The below error occurred while initializing the driver')
                print(str(err))
                sys.exit()
            prod_links = process_links(driver, processed_links, output3)
            scrape_prods(driver, prod_links, output1, output2)
            driver.quit()
            break
        except Exception as err: 
            print(f'Error: {err}')
            driver.quit()
            sleep(5)

    # removing the temp file
    if os.path.exists(output3):
        os.remove(output3) 
    print('-'*100)
    time = round(((time() - start)/60), 2)
    input(f'Process is completed successfully in {time} mins! Press any key to exit.')