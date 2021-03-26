import pandas as pd
from time import sleep
from random import randint
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests

from scraperuodas.util import generate_urls, extract_data, process_data


class Scraper():
    """
    This is a webscraper specifically tailored to scrape listings on aruodas.lt.

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

    def __init__(self, num_samples: int = 27, city: str = "Vilnius", max_price: int = 350):
        try:
            if not isinstance(num_samples, int) and not isinstance(city, str) and not isinstance(max_price, int):
                raise TypeError
            self.__num_samples = num_samples
            self.__city = city
            self.__max_price = max_price

        except TypeError as err:
            err.args('''One of the arguments is of wrong type.
               num_samples must be of type int, city must be of type str and max_price must be of type int''')

    def scrape_data(self, num_samples: int, keyword: str) -> pd.DataFrame:
        urls = generate_urls(self.__num_samples)
        ua = UserAgent()
        result = []

        for url in urls:
            # Sends the requests for the given urls and stores the responses
            resp = requests.get(url, params={"FOrder": "AddDate", "FPriceMax": "400"},
                                headers={"User-Agent": ua.random})
            soup = BeautifulSoup(resp.content, "html.parser")
            result = extract_data(soup, result)
            sleep(randint(1, 5))

        df = pd.DataFrame(result)
        df = process_data(df)
        return df
