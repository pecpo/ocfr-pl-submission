import json
import requests
from requests.auth import HTTPBasicAuth
from geminiFunctions import *
from prompts_and_sys_instructions import *

creds = json.load(open("credentials.json"))
auth = HTTPBasicAuth(creds["TBO_Hotel_API_USERNAME"], creds["TBO_Hotel_API_PASSWORD"])

def get_country_list():
    url = "http://api.tbotechnology.in/TBOHolidays_HotelAPI/CountryList?1=1"
    payload = {

    }
    response = requests.get(url, json=payload, auth=auth)
    # print(response.json)
    if(response.status_code == 200):
        return response.json()["CountryList"]
    return -1


def get_city_list(country_code):
    url = "http://api.tbotechnology.in/TBOHolidays_HotelAPI/CityList"
    payload = {
        "CountryCode": country_code
    }
    response = requests.post(url, json=payload, auth=auth)
    if(response.status_code == 200):
        return response.json()["CityList"]
    return -1





