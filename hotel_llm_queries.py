from geminiFunctions import *
from prompts_and_sys_instructions import *
from tbo_hotel_queries import *
def sort_hotels_for_user(city_code, chat_history):
    hotels_list = get_hotels_list(city_code)
    hotels_list = hotels_list["Hotels"]
    system_instruction = system_instruction_for_sorting_hotels
    history, chat, __ = start_chat(system_instruction)
    while True:
        try:
            history, chat = send_message(f"Based on this chat history, and the given json, sort the hotels. json : {hotels_list}. \n\n chat history : {chat_history} \n\n. Remember your response must be a valid python list as your response will be fed directly to eval function in python.", history, chat, system_instruction)

            response = history[-1]["parts"][0]["text"]
            print(response)
            for i in range(len(response)):
                if response[i] == "[":
                    response = response[i:]
                    break
            for i in range(len(response) - 1, -1, -1):
                if response[i] == "]":
                    response = response[:i + 1]
                    break
            print(response)
            lst = eval(response)
            return lst
        except Exception as e:
            print("Something went wrong in the sorting")
            print(e)
            continue

def get_hotel_description(hotel_code, chat_history):
    hotel_details = get_hotel_details(hotel_code)
    hotel_details = hotel_details["HotelDetails"]
    if 'Images' in hotel_details:
        hotel_details.pop("Images")
    system_instruction = system_instruction_for_hotel_description
    history, chat, __ = start_chat(system_instruction)
    while True:
        try:
            history, chat = send_message(f"Based on this chat history, and the given json, give the hotel description. json : {hotel_details}. \n\n chat history : {chat_history} \n\n. ", history, chat, system_instruction)
            response = history[-1]["parts"][0]["text"]
            return response
        except Exception as e:
            print("Something went wrong in the descriptioning")
            print(e)
            continue

