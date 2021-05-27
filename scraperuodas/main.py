from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import math
from time import sleep
import requests
from random import randint


class Scraperuodas:
    """
    Automated data collection tool (web-scraper) specifically tailored to scrape data on aruodas.lt.
    
    Parameters:
    
        num_samples (int): The number of samples of data to be scraped. One sample amounts to a single listing on
        a search results page. The minimum of 27 samples can be provided.
        
        city (str): The name of the city that the listings are based in.
        Default value of the parameter is "Vilnius".
        Cities the listings for which can currently be found on aruodas.lt:
        Vilnius, Kaunas, Klaipėda, Šiauliai, Panevėžys, Alytus, Palanga.
        
        max_price(int): Maximum price to limit the search results by.
        The parameter corresponds to the query parameter "MaxPrice".
        
    Returns:
    
        pd.DataFrame: Returns a dataframe with the following categories as columns:
        name of the district, name of the street, price (euros per month), price per square mater (abbreviated as price_per_sm),
        area (area of the room/apartment listed for rent in square meters), floor the room/apartment listed is on
        and the total number of floors on the building the apartment is on.
        The number of samples corresponds to the number of rows in the returned table.
        
    """
    
    def __init__(self) -> None:
        self.num_samples = 0
        self.max_price = 0

    def generate_urls(self, num_samples: int, city: str, max_price: int) -> list:
        # Note that there's 27 listings on a single page
        city_path = city
        page_path = 'puslapis/'
        query_params = {"FOrder": "AddDate", "FPriceMax": max_price}
        base_url = "https://www.aruodas.lt/butu-nuoma/{city_path}{page_path}{page_number}"
        urls = []

        if num_samples <= 27:
            url = base_url.format(city_path=city_path, page_path="", page_number="")
            urls.append(url)
            return urls

        else:
            num_pages = math.ceil(num_samples / 27)
            url = base_url.format(city_path=city_path, page_path="", page_number="")
            urls.append(url)

            for page in range(2, num_pages + 1):
                url = base_url.format(city_path=city_path, page_path=page_path, page_number=page)
                urls.append(url)
            return urls

    def extract_data(self, soup, results_list) -> list:  # Make sure that there is data within all the tags
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

    def process_data(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        data = dataframe
        data = data.apply(lambda x: x.explode())
        data = data.dropna()
        data['price'] = data['price'].str.replace("€", "").str.strip().astype(int)
        data['price_per_sm'] = data['price_per_sm'].str.replace("€/m²", "").str.replace(",", ".").str.strip().astype(
            float)
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
                pd.Timedelta))
        data['address'] = data['address'].str.replace("[", "").str.replace("]", "").str.replace("'", "")
        data['address'] = data['address'].str.split(",")
        data['address'] = data['address'].str[:2]
        data['district'], data['street'] = data['address'].str
        data = data.drop(columns="address")

        return data

    def scrape_data(self, num_samples: int = 27, city: str = "vilniuje", max_price=400) -> pd.DataFrame:
        self.num_samples = num_samples
        self.city = city
        self.max_price = max_price

        urls = self.generate_urls(self.num_samples, self.city, self.max_price)
        result = []

        for url in urls:
            ua = UserAgent()
            resp = requests.get(url, params={"FOrder": "AddDate", "FPriceMax": "400"},
                                headers={"User-Agent": ua.random})
            soup = BeautifulSoup(resp.content, "html.parser")
            result = self.extract_data(soup, result)
            sleep(randint(1, 5))

        df = pd.DataFrame(result)
        df = self.process_data(df)

        return df
