import requests
import math
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd


def find_maximum_page() -> int:  # will probably take query params as arguments
    """Finds the maximal number of pages that can be scraped given the arguments for num_samples and max_prices"""
    # might have to replace the url with place_holders
    ua = UserAgent()
    url = "https://www.aruodas.lt/butu-nuoma/vilniuje/?FOrder=AddDate&FPriceMax=350"
    headers = {"User-Agent": ua.random}

    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")

    # Find all the tags with page numbers between them
    pagination = soup.find("div", class_="pagination")
    page_arr = []

    # Strip the whitespace and append to the list if the element is numeric for there might be
    # characters such as "»" in the list
    for i in pagination.find_all("a", class_="page-bt"):
        page_number = i.text.strip()
        if page_number.isnumeric():
            page_arr.append(page_number)

    # Convert the elements in the list as integers
    page_arr = list(map(int, page_arr))

    # Find and return the largest element which represent the last page of the search results
    maximum_page = max(page_arr)
    return maximum_page


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
            max_pages = find_maximum_page()

            if num_pages <= max_pages:
                url = base_url.format(city_path=city_path, page_path="", page_number="")
                urls.append(url)

                for page in range(2, num_pages + 1):
                    url = base_url.format(city_path=city_path, page_path=page_path, page_number=page)
                    urls.append(url)

            else:
                num_samples = 4000
                num_pages = -(-num_samples // 27)
                max_pages = 16

                message = """You have requested to generate {num_samples} samples. In order to generate this number of samples,
                                      {num_pages} pages of search results would have to be scraped. However, there are only {max_pages} pages
                                      available given the criteria you selected. Please enter a number no larger than {max_samples} and 
                                      run the program again.
                                      """.format(num_samples=num_samples, num_pages=num_pages,
                                                 max_pages=max_pages,
                                                 max_samples=max_pages * 27)
                raise ValueError
    except ValueError as err:
        err.args(message)
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
