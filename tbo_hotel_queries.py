from tbo_general import *

#Assumption : tokenId is valid

def get_hotels_list(city_code):
    url = "http://api.tbotechnology.in/TBOHolidays_HotelAPI/TBOHotelCodeList"
    payload = {
        "CityCode": city_code,
        "IsDetailedResponse": "false"
    }
    try:
        response = requests.post(url, json=payload, auth=auth)
        if(response.status_code == 200):
            return response.json()
        else:
            return -1
    except:
        print("EXception in list method : ", e)
        return -1

def get_hotel_details(hotel_code):
    url = "http://api.tbotechnology.in/TBOHolidays_HotelAPI/Hoteldetails"
    payload = {
        "Hotelcodes": hotel_code,
        "Language": "en"
    }
    try:
        response = requests.post(url, json=payload, auth=auth)
        if(response.status_code == 200):
            return response.json()
        else:
            return -1
    except Exception as e:
        print("Exception in details method : ", e)
        return -1


