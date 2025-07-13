import json

def handle_multi_country(query_json):
    isMultiCountry = False
    if(type(query_json["CountryCode"]) == list):
        isMultiCountry = True
    lst = []
    if(not isMultiCountry):
        lst.append(query_json)
        return lst

    for i in range(len(query_json["CountryCode"])):
        temp_json = query_json.copy()
        temp_json["CountryCode"] = query_json["CountryCode"][i]
        lst.append(temp_json)
    return lst


def handle_multi_city(query_json_list):
    lst = []
    for curr_json in query_json_list:
        isMultiCity = False
        if(type(curr_json["CityId"]) == list):
            isMultiCity = True
        if(not isMultiCity):
            lst.append(curr_json)
            continue
        for i in range(len(curr_json["CityId"])):
            temp_json = curr_json.copy()
            temp_json["CityId"] = curr_json["CityId"][i]
            lst.append(temp_json)
    return lst

def handle_child_ages(query_json_list):
    for curr_json in range(len(query_json_list)):
        if(type(query_json_list[curr_json]["ChildAge"]) == list):
            if(len(query_json_list[curr_json]["ChildAge"]) > 0):
                for curr_age in query_json_list[curr_json]["ChildAge"]:
                    if(curr_age >= 18):
                        query_json_list[curr_json]["AdultCount"] += 1
                        query_json_list[curr_json]["ChildAge"].remove(curr_age)
                        query_json_list[curr_json]["ChildCount"] -= 1
                    if (curr_age < 0):
                        query_json_list[curr_json]["ChildAge"].remove(curr_age)
                        query_json_list[curr_json]["ChildCount"] -= 1
    return query_json_list

if __name__ == "__main__":
    js = {'CityId': ['122401', '109593'], 'CountryCode': 'TH', 'FromDate': '2024-01-18T00:00:00', 'ToDate': '2024-01-25T00:00:00', 'AdultCount': 2, 'ChildCount': 2, 'ChildAge': [19, 14], 'PreferredLanguage': 0, 'PreferredCurrency': 'INR', 'IsBaseCurrencyRequired': False, 'EndUserIp': '127.0.0.1', 'TokenId': 'generate-new-token', 'KeyWord': 'family getaway, luxurious, adventure, boat trips, snorkeling, kayaking, water sports, spa'}
    js = handle_multi_country(js)
    js = handle_multi_city(js)