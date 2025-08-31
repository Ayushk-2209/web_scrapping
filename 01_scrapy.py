from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import lxml
import pandas as pd
import re
from datetime import datetime
from selenium.webdriver.common.keys import Keys 


# Inputs to search

search_box_text = 'sports shoes for men'
website_link = 'https://www.flipkart.com/'

from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Initiating the browser
# Session start time
session_start_time = datetime.now().time()
print(f"Session Start Time: {session_start_time} ---------------------------> ")

driver = webdriver.Chrome()
try:
    driver.get(website_link)
    driver.maximize_window()

    # Try to close login popup if present
    try:
        close_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._2KpZ6l._2doB4z')))
        close_btn.click()
        print('Closed login popup.')
    except Exception as e:
        print('No login popup to close or error closing popup:', e)

    print('Waiting for search input...')
    try:
        search_input = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[autocomplete="off"]'))) 
    except TimeoutException:
        print('Search input not found. Exiting.')
        driver.quit()
        raise

    print('Typing in search input...') 
    search_input.send_keys(search_box_text) 
    print('Submitting search form...') 
    search_input.send_keys(Keys.RETURN) 
    print('Waiting for search results...') 
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[target="_blank"]')))
    except TimeoutException:
        print('Search results did not load. Exiting.')
        driver.quit()
        raise

    print('Collecting pagination links...') 
    all_pagination_links = []
    try:
        nav_links = driver.find_elements(By.CSS_SELECTOR, 'nav a')
        for a in nav_links:
            href = a.get_attribute('href')
            if href and href not in all_pagination_links:
                all_pagination_links.append(href)
    except Exception as e:
        print('Could not collect pagination links:', e)

    if len(all_pagination_links) < 2:
        print('Not enough pagination links found, constructing manually.')
        first_page = driver.current_url
        for i in range(2, 6):  # Only 5 pages for safety
            new_pagination_link = first_page.rstrip('/') + f'&page={i}'
            all_pagination_links.append(new_pagination_link)

    max_pages = 2  # Change this to a higher number after confirming it works
    all_pagination_links = all_pagination_links[:max_pages]

    print('Pagination Links Count:', len(all_pagination_links)) 
    print("All Pagination Links: ", all_pagination_links)

    print("Collecting Product Detail Page Links")
    all_product_links = []
    for idx, link in enumerate(all_pagination_links):
        print(f'Processing page {idx+1}/{len(all_pagination_links)}: {link}')
        try:
            driver.get(link)
            WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'rPDeLR')))
                all_products = driver.find_elements(By.CLASS_NAME, 'rPDeLR')
            except TimeoutException:
                print('Class rPDeLR not found, trying _1fQZEK')
                all_products = driver.find_elements(By.CLASS_NAME, '_1fQZEK')
            all_links = [element.get_attribute('href') for element in all_products if element.get_attribute('href')]
            print(f"{link} Done ------> Found {len(all_links)} products")
            all_product_links.extend(all_links)
        except Exception as e:
            print(f"Failed to process {link}: {e}")

    print('All Product Detail Page Links Captured: ', len(all_product_links)) 
    df_product_links = pd.DataFrame(all_product_links, columns=['product_links'])
    df_product_links = df_product_links.drop_duplicates(subset=['product_links'])

    print("Total Product Detail Page Links", len(df_product_links))
    df_product_links.to_csv('flipkart_product_links.csv', index = False)

except WebDriverException as e:
    print(f'WebDriverException occurred: {e}')
except Exception as e:
    print(f'Unexpected error: {e}')
finally:
    try:
        driver.close()
    except Exception:
        pass
    session_end_time = datetime.now().time()
    print(f"Session End Time: {session_end_time} ---------------------------> ")

# The code above is a complete script for scraping product links from Flipkart using Selenium.

#session start time
session_start_time = datetime.now().time()
print(f"Session Start Time: {session_start_time} ---------------------------> ")


#reading the csv file which contain all product links
df_product_links = pd.read_csv("flipkart_product_links.csv")

# Remove the below line to scrap all the products. For demonstration purpose we are scraping only 10 products
df_product_links = df_product_links.head(30)

all_product_links = df_product_links['product_links'].tolist()
print("Collecting Individual Product Detail Information")

#starting the browser
driver = webdriver.Chrome()


complete_product_details = []
unavailable_products = []
successful_parsed_urls_count = 0
complete_failed_urls_count = 0

for product_page_link in all_product_links:
    try: 
        driver.get(product_page_link)
        # Wait for the page to load by checking document.readyState
        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        WebDriverWait(driver, 20).until( EC.presence_of_element_located((By.CSS_SELECTOR, '[target="_blank"]')))
        #checking if product is available or not
        try:
            product_status =  driver.find_element(By.CLASS_NAME, 'Z8JjpR').text
            if product_status == 'Currently Unavailable' or product_status == 'Sold Out':
                unavailable_products.append(product_page_link)
                successful_parsed_urls_count += 1
                print(f"URL {successful_parsed_urls_count} completed --->")
        except:
            pass
        #brand
        brand =  driver.find_element(By.CLASS_NAME, 'mEh187').text
        #title       
        title = driver.find_element(By.CLASS_NAME, 'VU-ZEz').text
        title = re.sub(r'\s*\([^)]*\)', '', title)  #removing data withing parenthesis (color information)
        #price      
        price = driver.find_element(By.CLASS_NAME, 'Nx9bqj').text
        price = re.findall(r'\d+', price)
        price = ''.join(price)
        # Discount  
        try:
            discount = driver.find_element(By.CLASS_NAME, 'UkUFwK').text
            discount = re.findall(r'\d+', discount)
            discount = ''.join(discount)
            discount = int(discount) / 100
        except:
            discount = ''
        #for a new product, there will be no avg_rating and total_ratings    
        try:
            product_review_status = driver.find_element(By.CLASS_NAME, 'E3XX7J').text
            if product_review_status == 'Be the first to Review this product':
                avg_rating = ''
                total_ratings = ''
        except:
            avg_rating = driver.find_element(By.CLASS_NAME, 'XQDdHH').text
            total_ratings = driver.find_element(By.CLASS_NAME, 'Wphh3N').text.split(' ')[0]
            #remove the special character
            if ',' in total_ratings:
                total_ratings = int(total_ratings.replace(',', ''))
            else:
                total_ratings = int(total_ratings)
        # image_url
        try:
            image_url = driver.find_element(By.CSS_SELECTOR, 'img._396cs4').get_attribute('src')
        except Exception:
            image_url = ''
        successful_parsed_urls_count += 1
        print(f"URL {successful_parsed_urls_count} completed *******")
        complete_product_details.append([product_page_link, title, brand, price, discount, avg_rating, total_ratings, image_url])  
    except Exception as e:
        print(f"Failed to establish a connection for URL {product_page_link}:  {e}")
        unavailable_products.append(product_page_link)
        complete_failed_urls_count += 1
        print(f"Failed URL Count {complete_failed_urls_count}")


#create pandas dataframe 
df = pd.DataFrame(complete_product_details, columns = ['product_link', 'title', 'brand', 'price', 'discount', 'avg_rating', 'total_ratings', 'image_url'])
#duplicates processing
df_duplicate_products = df[df.duplicated(subset=['brand', 'price', 'discount', 'avg_rating', 'total_ratings'])]
df = df.drop_duplicates(subset=['brand', 'price', 'discount', 'avg_rating', 'total_ratings'])
#unavailable products
df_unavailable_products = pd.DataFrame(unavailable_products, columns=['link'])


#prining the stats
print("Total product pages scrapped: ", len(all_product_links))
print("Final Total Products: ", len(df))
print("Total Unavailable Products : ", len(df_unavailable_products))
print("Total Duplicate Products: ", len(df_duplicate_products))


#saving all the files
df.to_csv('flipkart_product_data.csv', index = False)
df_unavailable_products.to_csv('unavailable_products.csv', index = False)
df_duplicate_products.to_csv('duplicate_products.csv', index = False)


driver.close()
session_end_time = datetime.now().time()
print(f"Session End Time: {session_end_time} ---------------------------> ")