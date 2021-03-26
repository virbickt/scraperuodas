import requests
import math
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd


def generate_urls(num_samples: int, max_price: int) -> list:
    """Generates urls for the search results given the parameter values for num_samples, city and max_price"""
    city_path = 'vilniuje/'
    page_path = 'puslapis/'
    base_url = "https://www.aruodas.lt/butu-nuoma/{city_path}{page_path}{page_number}"
    query_params = {"FOrder": "AddDate", "FPriceMax": max_price}
    urls = []
    try:
        if num_samples <= 27:

            url = base_url.format(city_path=city_path, page_path="", page_number="")
            urls.append(url)

        else:

            num_pages = math.ceil(num_samples / 27)
            for page in range(2, num_pages + 1):
                url = base_url.format(city_path=city_path, page_path=page_path, page_number=page)
                urls.append(url)
    except:
        pass

    return urls


def extract_data(resp, results_list) -> list:  # Make sure that there is data within all the tags
    """Extracts data given the default categories: address (to be later processed into district and street separately)
    price, price per square meter, date_added (later to be processed into a absolute date
    instead of the default relative date), number_of_rooms, area (in square meters) and floors
    (to be processed into separate categories for the floor the apartment is on and the total number of floors
    on the building)"""
    listings = soup.select("tr.list-row")

    for listing in listings:
        listing_data = {"address": [a.img['title'] for a in listing.find_all("td", class_="list-img")],
                        "price": [x.text for x in listing.find_all("span", class_="list-item-price")],
                        "price_per_sm": [x.text.strip() for x in listing.find_all("span", class_="price-pm")],
                        "date_added": [x.text for x in listing.find_all("p", class_="flat-rent-dateadd")],
                        "number_of_rooms": [x.text.strip() for x in listing.find_all("td", class_="list-RoomNum")],
                        "area": [x.text.strip() for x in listing.find_all("td", class_="list-AreaOverall")],
                        "floors": [x.text.strip() for x in listing.find_all("td", class_="list-Floors")]}
        results_list.append(listing_data)

    return results_list


def process_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Processes the extracted data so there's"""
    data = dataframe
    data = data.apply(lambda x: x.explode())
    data = data.dropna()
    data['price'] = data['price'].str.replace("€", "").str.strip().astype(int)
    data['price_per_sm'] = data['price_per_sm'].str.replace("€/m²", "").str.replace(",", ".").str.strip().astype(float)
    data['number_of_rooms'] = data['number_of_rooms'].str.strip().astype(int)
    data['area'] = data['area'].str.strip().astype(float)
    data['floors'] = data['floors'].str.split('/')
    data['floor_on'], data['floors_total'] = zip(*data['floors'])
    data = data.drop(columns='floors')
    data['date_added'] = data['date_added'].str.replace("Prieš", "")
    data['date_added'] = data['date_added'].str.replace("min.", "minutes").str.replace("val.", "hours").str.replace(
        "d.", "days").str.replace("mėn.", "months").str.replace("just now", "1 minutes")
    data['date_added'] = data['date_added'] + " ago"
    data = data.drop(data[data['date_added'].str.contains("months")].index)
    data['date_added'] = (
            datetime.datetime.now() - data['date_added'].str.extract('(.*)\s+ago', expand=False).apply(
        pd.Timedelta)
    )
    data['address'] = data['address'].str.replace("[", "").str.replace("]", "").str.replace("'", "")
    data['address'] = data['address'].str.split(",")
    data['address'] = data['address'].str[:2]
    data['district'], data['street'] = data['address'].str
    data = data.drop(columns="address")

    return data
