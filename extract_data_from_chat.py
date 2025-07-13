from geminiFunctions import *

# from sightseeing_llm_queries import *
# from tbo_general import *
from tbo_sightseeing_queries import *
from prompts_and_sys_instructions import *
from make_json_searchable import *
import firebase_handler as fh
import tbo_hotel_queries as tbo_hotel
###for testing

# print("Starting")
# with open("init_chat_history.txt", "r") as f:
#     history = eval(f.read())
# print(history)

# print(type(history))
# print(history)

attractions_list = None
def get_country_code(history, chat=None):
    country_list = get_country_list()
    system_instruction = system_instruction_for_getting_country_code
    newHistory, newChat, __ = start_chat(system_instruction)
    newHistory,chat = send_message(f"Based on this chat history, and the given json, extract the country code. json : {country_list}. \n\n chat history : {history}", newHistory, newChat, system_instruction)
    return newHistory[-1]["parts"][0]["text"]

# country_code = get_country_code(history, chat)
# print(country_code)

def get_city_name_from_city_id(country_id, city_id):
    city_list = get_city_list(country_id)
    for city in city_list:
        if city["Code"] == city_id:
            return city["Name"]
    return -1
def get_user_city_list(history, city_list_complete):
    system_instruction = system_instruction_for_getting_city_code
    newHistory, newChat, _ = start_chat(system_instruction)
    newHistory, newChat = send_message(f"Based on this chat history, and the given city list, extract the city list. json : {str(city_list_complete)}. \n\n chat history : {str(history)}", newHistory, newChat, system_instruction)
    return newHistory[-1]["parts"][0]["text"]
def create_user_detail_json(history, sessionid, chat=None):
    system_instruction = system_instruction_for_creating_user_detail_json
    newHistory, newChat, _ = start_chat(system_instruction)
    print("binsearching 1")
    newHistory, newChat = send_message("Populate the json with the given history as expected. Here's the chat history : \n\n" + str(history), newHistory, newChat, system_instruction)
    country_code = get_country_code(history, chat)
    country_code = country_code.strip()
    print("binsearching 2")
    fh.set_country_code(sessionid, country_code)
    city_list_complete = get_city_list(country_code)
    print("binsearching 3")
    city_list = get_user_city_list(history, city_list_complete)
    newHistory, newChat = send_message(f"Based on the given country code, and the city list(all have to be added), and the chat history, give me the final json. You're supposed to check if the country code is correctly populated, and the CityId is correctly populated.Note that Country Code is a two letter word, for example AE for Dubai. City code is a 6 digit numeric string, for example 148767. In case there are multiple cities, add them as a list and in case there are multiple countries, add them as a list too. Country code : {country_code}, CityList : {city_list}, chat history : {str(history)}", newHistory, newChat, system_instruction)
    print(newHistory[-1]["parts"][0]["text"])
    while True:
        try:
            if city_list[0] == "`":
                city_list = city_list[7:]
                city_list = city_list[:-4]
            city_list = eval(city_list)
            break
        except Exception as e:
            print("Exception in city list eval")
            print(e)
            city_list = get_user_city_list(str(history) + "Remember that your output must be a valid python string", city_list_complete)
            continue
    return newHistory[-1]["parts"][0]["text"], city_list

def get_user_json(history, sessionid):
    chat = None
    js, city_list = create_user_detail_json(history, sessionid, chat)

    print("step 1 doen")
    if(js[0] == '`'):
        js = js[7:]
        js = js[:-4]

    js  = convert_string_to_json(js)
    print("1")
    js = handle_multi_country(js)
    print("2")
    js = handle_multi_city(js)
    print("3")
    js = handle_child_ages(js)
    print("4")
    print(js)
    lst = get_attractions_list_for_multiple_destinations(js)
    print("5")
    attractions_list = lst
    print("6")
    return attractions_list, city_list






