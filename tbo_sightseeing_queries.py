import requests
from tbo_general import *
import json

from geminiFunctions import *
from prompts_and_sys_instructions import *



def authenticate():
    creds = json.load(open("credentials.json"))
    username = creds["TBO_SIGHTSEEING_API_USERNAME"]
    password = creds["TBO_SIGHTSEEING_API_PASSWORD"]
    client_id = creds["TBO_SIGHTSEEING_API_CLIENT_ID"]
    url = "https://Sharedapi.tektravels.com/SharedData.svc/rest/Authenticate"
    payload = {
        "ClientId": client_id,
        "UserName": username,
        "Password": password,
        "EndUserIp": "192.168.11.120"
    }
    response = requests.post(url, json=payload)
    if (response.status_code == 200):
        return response.json()["TokenId"]
    return -1


trace_id = -1


def get_attractions_list(country_code, city_id, from_date, to_date, adult_count, child_count, child_age,
                         preferred_currency, keyword=""):
    global trace_id
    print("here")
    token_id = authenticate()
    print("here")
    url = "https://SightseeingBE.tektravels.com/SightseeingService.svc/rest/Search"
    payload = {
        "CityId": city_id,
        "CountryCode": country_code,
        "FromDate": from_date,  # format : 2025-04-13T00:00:00
        "ToDate": to_date,
        "AdultCount": adult_count,
        "ChildCount": child_count,
        "ChildAge": child_age,
        "PreferredLanguage": 0,
        "PreferredCurrency": preferred_currency,
        "IsBaseCurrencyRequired": False,
        "EndUserIp": "192.168.5.56",
        "TokenId": token_id,
        "KeyWord": ""
    }
    response = requests.post(url, json=payload)
    print(payload)
    if (response.status_code == 200):
        trace_id = response.json()["Response"]["TraceId"]
        return response.json()
    return -1


def get_attraction_details(result_index):
    token_id = authenticate()
    url = "https://SightseeingBE.tektravels.com/SightseeingService.svc/rest/GetAvailability"
    payload = {
        "ResultIndex": result_index,
        "EndUserIp": "192.168.5.56",
        "TraceId": trace_id,
        "TokenId": token_id
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    return -1


def get_attractions_list_for_multiple_destinations(list_of_jsons):
    attractions_lst = []
    for curr_json in list_of_jsons:
        print(curr_json)
        curr_list = get_attractions_list(curr_json["CountryCode"], curr_json["CityId"], curr_json["FromDate"],
                                         curr_json["ToDate"], curr_json["AdultCount"], curr_json["ChildCount"],
                                         curr_json["ChildAge"], curr_json["PreferredCurrency"])
        if (curr_list == -1):
            continue
        attractions_lst.append(curr_list)
    return attractions_lst
