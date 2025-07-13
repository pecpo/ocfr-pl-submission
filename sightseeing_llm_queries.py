from extract_data_from_chat import get_user_json, get_city_name_from_city_id
from geminiFunctions import *
from prompts_and_sys_instructions import *
import json
import firebase_handler as fh
import services
import threading
from threading import Thread
from bing_image_urls import bing_image_urls
from timings import *
from datetime import datetime
from tbo_hotel_queries import *
from hotel_llm_queries import *
# with open("attractions.txt", encoding="utf-8") as f:
#     attractions = f.read()
#
# with open("init_chat_history.txt") as f:
#     chat_history = (f.read())

def retry_until_success(func, *args):
    while True:
        try:
            ans = func(*args)
            if ans is not None:
                return ans
            else:
                continue
        except Exception as e:
            print(f"Error: {e} in function {str(func.__name__)}. Retrying...")


def shortlist_attractions(attractions_list, chat_history, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_shortlisting_attractions
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and attractions list, shortlist the attractions. Attractions list : {attractions_list} \n\n chat history : {chat_history} ",
        history, chat, system_instruction,model)
    return history[-1]["parts"][0]["text"]


def cluster_groups_by_geographical_data(attractions_list, chat_history, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_clustering_attractions_geographically
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and attractions list, cluster the attractions based on their geographical data. Attractions list : {attractions_list} \n\n chat history : {chat_history} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def get_timings_for_attractions(attractions_list, chat_history, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_getting_best_times_to_visit
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and attractions list, give the best times for the attractions based on the api results and google saerch and your training data. Attractions list : {attractions_list} \n\n chat history : {chat_history} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def get_budget_reasoning_for_attractions(attractions_list, chat_history, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_budget_reasoning
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and attractions list, give the budget based attractions. Attractions list : {attractions_list} \n\n chat history : {chat_history} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def get_day_wise_itinerary(chat_history, geographical_reasoning, time_based_reasoning, budget_reasoning, attractions,
                           shortlisted_attractions, duration_analysis, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_day_wise_planning
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history, geographical reasoning, time based reasoning ,budget reasoning, duration analysis, original(complete attractions list) and shortlisted_attraction list(done by another llm based on what it thought are user's preferences) give the day wise itinerary. \n\n chat history : {chat_history} \n\n geographical reasoning : {geographical_reasoning} \n\n time based reasoning : {time_based_reasoning} \n\n budget reasoning : {budget_reasoning} \n\n duration analysis : {duration_analysis} \n\n original attractions list : {attractions}, \n\n shortlisted attractions : {shortlisted_attractions}",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def summarise_attractions(attractions_list, chat_history, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_summarising_search_json
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and attractions list, summarise the attractions. Keep in mind that your output is the input for other llm agents which will perform further analysis on the attractions so your description of the attraction must be detailed enough for it to be helpful to any and all cases of analysis. Attractions list : {attractions_list} \n\n chat history : {chat_history} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def remove_redundant_attractions(summarised_attractions_list, chat_history, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_removing_redundant_attractions
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and attractions list, remove the redundant attractions. Attractions list : {summarised_attractions_list} \n\n chat history : {chat_history} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def get_duration_analysis_of_attractions(summarised_attractions, chat_history, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_duration_analysis
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and attractions list, give the duration analysis of the attractions. Attractions list : {summarised_attractions} \n\n chat history : {chat_history} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def get_intraday_planning(attractions, chat_history, day_wise_itinerary, duration_analysis, clustered_attractions,
                          time_based_attractions, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_intraday_planning
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history, attractions, day wise itinerary, duration analysis, clustered attractions, time based attractions and budget reasoned attractions, give the intraday planning. \n\n chat history : {chat_history} \n\n attractions : {attractions} \n\n day wise itinerary : {day_wise_itinerary} \n\n duration analysis : {duration_analysis} \n\n clustered attractions : {clustered_attractions} \n\n time based attractions : {time_based_attractions} \n\n",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def add_free_attractions_on_route(chat_history, day_wise_itinerary, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_free_attraction_addition
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and day wise itinerary, add the free attractions on the route. \n\n chat history : {chat_history} \n\n day wise itinerary : {day_wise_itinerary} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def get_route_to_be_followed(chat_history, current_itinerary, free_attractions, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_route_planning
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history, free attractions and current itinerary, give the route to be followed. \n\n chat history : {chat_history} \n\n current itinerary : {current_itinerary}, \n\n free attractions : {free_attractions} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]


def add_restaurants_on_route(chat_history, current_itinerary, model="gemini-2.0-flash-thinking-exp"):
    system_instruction = system_instruction_for_adding_restaurants_on_the_route
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and current itinerary, add the restaurants on the route. \n\n chat history : {chat_history} \n\n current itinerary : {current_itinerary} ",
        history, chat, system_instruction, model)
    return history[-1]["parts"][0]["text"]

def check_name_price(activity, attractions):
    print("checking name price")
    if 'SightseeingCode' not in activity:
        return True
    for curr_city in attractions:
        print("Passed phase 1")
        if curr_city is not None:
            curr_response = curr_city['Response']
            curr_attractions = curr_response['SightseeingSearchResults']
            print("Passed phase 2")
            if curr_attractions is not None:
                for attraction in curr_attractions:
                    if attraction['SightseeingCode'] == activity['SightseeingCode']:
                        print("Passed phase 3")
                        print(attraction['SightseeingName'])
                        print(activity['SightseeingName'])
                        if attraction['SightseeingName'] == activity['SightseeingName'] or True:
                            print("Phase 4 passed")
                            print(activity)
                            curr_price = activity['price']
                            print("Phase 5 passed")
                            their_list = list(attraction['Price'].values())
                            print("Phase 6 passed")
                            if curr_price not in their_list:
                                print("Phase 7 passed")
                                return False
                            else:
                                return True
                        else:
                            return False
    return True
def verify_day_json(day_json, attractions):
    day_json = day_json['complete_itinerary']
    for day, activity_list in day_json.items():
        for activity in activity_list:
            if activity['SightseeingCode'] is not None:
                check = check_name_price(activity, attractions)
                if check:
                    return True
                return False

def has_duplicates(curr_json, attractions_set):
    print("checking for duplicates")
    curr_json = curr_json['complete_itinerary']
    for day, activity_list in curr_json.items():
        for activity in activity_list:
            if activity['SightseeingCode'] in attractions_set:
                return True
            attractions_set.add(activity['SightseeingCode'])
    return False

def timings_match(curr_json, dubai_attraction_timings):
    print("doing timings match")
    curr_json = curr_json['complete_itinerary']
    dubai_attractions = dict()
    count = 0
    for attraction in dubai_attraction_timings:
        dubai_attractions[attraction['SightseeingCode']] = count
        count += 1

    for day, activity_list in curr_json.items():
        for activity in activity_list:
            if activity is not None and activity['SightseeingCode'] in dubai_attractions:
                end_str = activity['ToDate'].split('T')[1]
                start_str = activity['FromDate'].split('T')[1]
                end = datetime.strptime(end_str, '%H:%M:%S')
                start = datetime.strptime(start_str, '%H:%M:%S')
                actual_end_str = dubai_attraction_timings[dubai_attractions[activity['SightseeingCode']]]['opening_time']
                actual_start_str = dubai_attraction_timings[dubai_attractions[activity['SightseeingCode']]]['closing_time']
                actual_end = datetime.strptime(actual_end_str, '%H:%M:%S')
                actual_start = datetime.strptime(actual_start_str, '%H:%M:%S')
                if end > actual_end or start < actual_start:
                    return False
                return True
    return True
def get_itinerary_json(itinerary, attractions, chat_history, shortlisted_attractions, num_days, model="gemini-2.0-flash-exp"):
    final_json = [None] * num_days  # Pre-allocate list with None values
    attractions_set = set()
    def process_day(day_index):
        while True:
            try:
                system_instruction = system_instruction_for_getting_itinerary_json
                history, chat, _ = start_chat(system_instruction)
                history, chat = send_message(
                    f"Based on the given chat history, itinerary, attractions with their justifications for the user and tbo's api data for searching attractions in the given city, create the json for day {day_index+1}. \n\n tbo's api result : {attractions} \n\n itinerary : {itinerary}, \n\n chat history : {chat_history} \n\n justifications : {shortlisted_attractions}", 
                    history, chat, system_instruction, model
                )
                output_json = history[-1]["parts"][0]["text"]
                str_json = str(output_json)
                if str_json[0] == '`':
                    str_json = str_json[7:]
                    str_json = str_json[:-4]
                curr_json = convert_string_to_json(str_json)
                # if verify_day_json(curr_json, attractions):
                    # and not has_duplicates(curr_json, attractions_set) and timings_match(curr_json, dubai_attraction_timings)
                final_json[day_index] = convert_string_to_json(str_json)
                break
            except Exception as e:
                print(f"Retrying json for day {day_index+1}")
                print(e)
                continue

    # Create and start threads for each day
    threads = []
    for i in range(num_days):
        thread = Thread(target=process_day, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return final_json


def get_tbo_description(output_json, attractions):
    system_instruction = system_instruction_for_adding_tbo_description
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given output json and attractions, add the tbo description to the attractions. \n\n output json : {output_json} \n\n attractions : {attractions} ",
        history, chat, system_instruction)
    return history[-1]["parts"][0]["text"]


def get_llm_description(chat_history, itinerary):
    system_instruction = system_instruction_for_getting_llm_justifications
    history, chat, _ = start_chat(system_instruction)
    history, chat = send_message(
        f"Based on the given chat history and itinerary, give the llm description. \n\n chat history : {chat_history} \n\n itinerary : {itinerary} ",
        history, chat, system_instruction)
    return history[-1]["parts"][0]["text"]


import json


def populate_tbo_descriptions(itinerary_json, tbo_description_json):
    """
    Populates the 'tbo_description' field of each attraction in the itinerary with a summary from the corresponding entry in the tbo description JSON.

    Args:
        itinerary_json (str): A JSON string representing the complete itinerary where the key is complete_itinerary.
        tbo_description_json (str): A JSON string where keys are attraction names and values are the tbo descriptions.

    Returns:
        str: A JSON string representing the updated itinerary JSON with populated 'tbo_description' fields.
    """

    try:
        itinerary = json.loads(itinerary_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding itinerary JSON: {e}")

    try:
        tbo_descriptions = json.loads(tbo_description_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding TBO descriptions JSON: {e}")

    if 'complete_itinerary' not in itinerary:
        raise ValueError("Invalid itinerary json, 'complete_itinerary' key not found")

    for day, day_data in itinerary['complete_itinerary'].items():
        if isinstance(day_data, list):
            for activity in day_data:
                if 'SightseeingName' in activity and activity['SightseeingName'] in tbo_descriptions:
                    activity['tbo_description'] = tbo_descriptions[activity['SightseeingName']]
                else:
                    pass
                    # print(
                    #     f"Warning: No matching TBO description found for activity: {activity.get('SightseeingName', 'Unknown')}, skipped")
        elif isinstance(day_data, dict) and 'intraday_plan' in day_data:
            for time_slot, slot_data in day_data['intraday_plan'].items():
                if isinstance(slot_data, dict) and 'attractions' in slot_data:
                    for activity in slot_data['attractions']:
                        if 'SightseeingName' in activity and activity['SightseeingName'] in tbo_descriptions:
                            activity['tbo_description'] = tbo_descriptions[activity['SightseeingName']]
                        else:
                            pass
                            # print(
                            #     f"Warning: No matching TBO description found for activity: {activity.get('SightseeingName', 'Unknown')}, skipped")

    return json.dumps(itinerary, indent=2)


def populate_llm_descriptions(itinerary_json, llm_description_json):
    """
    Populates the 'llm_description' field of each attraction in a TBO-like itinerary JSON object.

    Args:
        itinerary_json (str): A JSON string representing a complete itinerary, with TBO-like structure.
        llm_description_json (str): A JSON string where keys are attraction names and values are personalized justifications.

    Returns:
        str: A JSON string representing the updated itinerary JSON with populated 'llm_description' fields.
    """

    try:
        itinerary = json.loads(itinerary_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding itinerary JSON: {e}")

    try:
        llm_descriptions = json.loads(llm_description_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding LLM descriptions JSON: {e}")

    if 'complete_itinerary' not in itinerary:
        raise ValueError("Invalid itinerary json, 'complete_itinerary' key not found")

    for day, day_data in itinerary['complete_itinerary'].items():
        if isinstance(day_data, list):
            for activity in day_data:
                if 'SightseeingName' in activity and activity['SightseeingName'] in llm_descriptions:
                    activity['llm_description'] = llm_descriptions[activity['SightseeingName']]
                else:
                    pass
                    # print(
                    #     f"Warning: No matching LLM description found for activity: {activity.get('SightseeingName', 'Unknown')}, skipping.")
        elif isinstance(day_data, dict) and 'intraday_plan' in day_data:
            for time_slot, slot_data in day_data['intraday_plan'].items():
                if isinstance(slot_data, dict) and 'attractions' in slot_data:
                    for activity in slot_data['attractions']:
                        if 'SightseeingName' in activity and activity['SightseeingName'] in llm_descriptions:
                            activity['llm_description'] = llm_descriptions[activity['SightseeingName']]
                        else:
                            pass
                            # print(
                            #     f"Warning: No matching LLM description found for activity: {activity.get('SightseeingName', 'Unknown')}, skipping.")
    return json.dumps(itinerary, indent=2)


# print(attractions)

# summarised_attractions = retry_until_success(summarise_attractions, attractions, chat_history)
#
# redundancy_removed_attractions = retry_until_success(remove_redundant_attractions, summarised_attractions, chat_history)
#
# shortlisted_attractions = retry_until_success(shortlist_attractions, redundancy_removed_attractions, chat_history)
#
# duration_analysis = retry_until_success(get_duration_analysis_of_attractions, shortlisted_attractions, chat_history)
# clustered_attractions = retry_until_success(cluster_groups_by_geographical_data, shortlisted_attractions, chat_history)
# time_based_attractions = retry_until_success(get_timings_for_attractions, shortlisted_attractions, chat_history)
# budget_reasoned_attractions = retry_until_success(get_budget_reasoning_for_attractions, shortlisted_attractions, chat_history)
#
# day_wise_itinerary = retry_until_success(get_day_wise_itinerary, chat_history, clustered_attractions, time_based_attractions, budget_reasoned_attractions, attractions, shortlisted_attractions, duration_analysis)
#
# free_attractions_added = retry_until_success(add_free_attractions_on_route, chat_history, day_wise_itinerary)
#
# intraday_planning = retry_until_success(get_intraday_planning, attractions, chat_history, day_wise_itinerary, duration_analysis, clustered_attractions, time_based_attractions)
# route_to_be_followed = retry_until_success(get_route_to_be_followed, chat_history, intraday_planning, free_attractions_added)
# restaurants_added = retry_until_success(add_restaurants_on_route, chat_history, route_to_be_followed)
#
# if restaurants_added[0] == '`':
#     restaurants_added = restaurants_added[7:]
#     restaurants_added = restaurants_added[:-4]
# output_json = convert_string_to_json(restaurants_added)
# num_days = len(output_json['itinerary_with_restaurants'])
# print(num_days)
#
# temp_json = retry_until_success(get_itinerary_json, restaurants_added, attractions, chat_history,shortlisted_attractions, num_days)
#
# output_json = {}
# for i in temp_json:
#     curr_val = 0
#     if "complete_itinerary" in i:
#         curr_val = i["complete_itinerary"]
#     else:
#         curr_val = i
#     output_json = output_json | curr_val
# print(output_json)
#
# print(output_json)
#
# with open("itinerary.json", "w") as f:
#     json.dump(output_json, f)

def populate_tbo_descriptions(itinerary_json, tbo_descriptions):
    """
    Populates TBO descriptions into the itinerary JSON.

    Args:
        itinerary_json (dict): The complete itinerary JSON
        tbo_descriptions (dict): Dictionary mapping SightseeingCode to descriptions

    Returns:
        dict: Updated itinerary JSON with TBO descriptions
    """
    for curr_attraction in tbo_descriptions:
        for day in itinerary_json:
            for activity in itinerary_json[day]:
                if activity['SightseeingCode'] == curr_attraction:
                    activity['tbo_description'] = tbo_descriptions[curr_attraction]
    return itinerary_json


def populate_llm_descriptions(itinerary_json, llm_descriptions):
    """
    Populates TBO descriptions into the itinerary JSON.

    Args:
        itinerary_json (dict): The complete itinerary JSON
        tbo_descriptions (dict): Dictionary mapping SightseeingCode to descriptions

    Returns:
        dict: Updated itinerary JSON with TBO descriptions
    """
    for curr_attraction in llm_descriptions:
        for day in itinerary_json:
            for activities in itinerary_json[day]:
                for activity in itinerary_json[day][activities]:
                    if activity['SightseeingCode'] == curr_attraction:
                        activity['llm_description'] = llm_descriptions[curr_attraction]
    return itinerary_json


# tbo_descriptions = get_tbo_description(output_json, attractions)
#
# print(tbo_descriptions)
# if tbo_descriptions[0] == '`':
#     tbo_descriptions = tbo_descriptions[7:]
#     tbo_descriptions = tbo_descriptions[:-4]
#     tbo_descriptions = convert_string_to_json(tbo_descriptions)
#
# print(output_json)
# output_json = populate_tbo_descriptions((output_json), (tbo_descriptions))
# print(output_json)
#
# llm_descriptions = get_llm_description(chat_history, output_json)
#
# output_json = populate_llm_descriptions(output_json, llm_descriptions)
#
# print(output_json)
#
# with open("itinerary.json", "w") as f:
#     json.dump(output_json, f)
def get_hotel_recommendations(city_list, chat_history, session_id):
    """
    For each city in the given city_list, this function retrieves the TBO hotels,
    sorts them using Gemini, and picks the best hotel. The per-city processing has
    been parallelized with multithreading. After collecting the results, the function
    calls the Gemini API to generate hotel recommendations. Finally, the response is
    returned from the LLM conversation.
    """
    city_list = set(city_list)
    city_list = list(city_list)
    print(city_list)
    time.sleep(10)
    from threading import Thread

    country_code = fh.get_country_code(session_id)
    results = [None] * len(city_list)

    def process_city(city_code, index):
        while True:
            try:
                hotels_data = get_hotels_list(city_code)
                if hotels_data == -1:
                    break
                if "Hotels" not in hotels_data:
                    break

                print(hotels_data)
                # hotels_data = hotels_data["Hotels"]
                # Use the chat history to sort hotels via the LLM
                sorted_hotels = sort_hotels_for_user(city_code, chat_history)
                chosen_hotel = sorted_hotels[0]
                hotel_details = get_hotel_details(chosen_hotel)
                if "Images" in hotel_details:
                    hotel_details.pop("Images")
                print("Getting city_name")
                city_name = get_city_name_from_city_id(country_code, city_code)
                print("putting into results")
                results[index%len(results)] = {str(city_name): str(hotel_details)}
                break
            except Exception as e:
                print(f"Error processing city {city_code}: {e.with_traceback()}")
                continue
                # results[index] = {str(get_city_name_from_city_id(country_code, city_code)): "Error retrieving hotel details"}

    # Create and start threads for each city code
    threads = []
    for idx, city_code in enumerate(city_list):
        thread = Thread(target=process_city, args=(city_code, idx))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    city_wise_best_hotels = results
    system_instruction = system_instruction_for_hotel_recommendation
    history, chat, _ = start_chat(system_instruction)
    prompt = (
        f"Based on the given chat history and this list of hotels which are given to you, "
        f"recommend the hotels. Keep in mind that you have to give the GREATEST weightage "
        f"to the chat history and the preferences and don't give too many hotel shifts unless asked for it. "
        f"Here's the chat history: {str(chat_history)}\n\n"
        f"Here's the list of hotels: {str(city_wise_best_hotels)}"
    )
    history, chat = send_message(prompt, history, chat, system_instruction, model="gemini-2.0-flash")
    print("recommendations : \n", history[-1]["parts"][0]["text"])
    return history[-1]["parts"][0]["text"]
def get_itinerary_after_chat(chat_history, sessionid, e):
    fh.set_status(sessionid, "Finding attractions for you")
    attractions, city_list = retry_until_success(get_user_json, chat_history, sessionid)
    fh.set_city_ids(sessionid, city_list)
    if e:
        hotel_recommendations = get_hotel_recommendations(city_list, chat_history, sessionid)
        chat_history[-1]["parts"][0]["text"] += "These are my hotel preferences which I asked from another LLM. These may not be very accurate, but you may want to look into it for a better idea\n\n" + str(hotel_recommendations)
    thread = threading.Thread(target=services.addAllAttractions, args=(attractions, sessionid))
    thread.start()
    print("step 1 done")
    summarised_attractions = retry_until_success(summarise_attractions, attractions, chat_history)
    print("step 2 done")
    fh.set_status(sessionid, "Removing repetitions")
    redundancy_removed_attractions = retry_until_success(remove_redundant_attractions, summarised_attractions,
                                                         chat_history)
    print("step 3 done")
    fh.set_status(sessionid, "Shortlisting attractions for you")
    shortlisted_attractions = retry_until_success(shortlist_attractions, redundancy_removed_attractions, chat_history)
    print("step 4 done")
    
    # Create thread-safe containers for results
    results = {
        'duration_analysis': None,
        'clustered_attractions': None,
        'time_based_attractions': None,
        'budget_reasoned_attractions': None
    }

    # Define thread functions
    def run_duration_analysis():
        results['duration_analysis'] = retry_until_success(get_duration_analysis_of_attractions, shortlisted_attractions, chat_history, "gemini-2.0-flash")

    def run_clustering():
        results['clustered_attractions'] = retry_until_success(cluster_groups_by_geographical_data, shortlisted_attractions, chat_history, "gemini-2.0-flash-exp")

    def run_timing_analysis():
        results['time_based_attractions'] = retry_until_success(get_timings_for_attractions, shortlisted_attractions, chat_history, "gemini-2.0-flash-exp")

    def run_budget_analysis():
        results['budget_reasoned_attractions'] = retry_until_success(get_budget_reasoning_for_attractions, shortlisted_attractions, chat_history, "gemini-2.0-flash-exp")

    # Create and start threads
    threads = [
        Thread(target=run_duration_analysis),
        Thread(target=run_clustering),
        Thread(target=run_timing_analysis),
        Thread(target=run_budget_analysis)
    ]

    fh.set_status(sessionid, "Analyzing attractions in parallel")
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("Parallel processing complete")
    
    fh.set_status(sessionid, "Getting itinerary's first draft")
    day_wise_itinerary = retry_until_success(
        get_day_wise_itinerary, 
        chat_history, 
        results['clustered_attractions'],
        results['time_based_attractions'], 
        results['budget_reasoned_attractions'], 
        attractions,
        shortlisted_attractions, 
        results['duration_analysis']
    )
    print("step 10 done")
    fh.set_status(sessionid, "Refining itinerary")
    free_attractions_added = retry_until_success(add_free_attractions_on_route, chat_history, day_wise_itinerary)
    print("step 11 done")
    fh.set_status(sessionid, "Figuring out what to do when")
    print("step 12 done")
    intraday_planning = retry_until_success(get_intraday_planning, attractions, chat_history, day_wise_itinerary,
                                            results['duration_analysis'], results['clustered_attractions'], results['time_based_attractions'])
    print("step 13 done")
    fh.set_status(sessionid, "Planning best paths to take")
    route_to_be_followed = retry_until_success(get_route_to_be_followed, chat_history, intraday_planning,
                                               free_attractions_added, "gemini-2.0-flash-exp")
    print("step 14 done")
    fh.set_status(sessionid, "Adding restaurants")
    restaurants_added = retry_until_success(add_restaurants_on_route, chat_history, route_to_be_followed, "gemini-2.0-flash-exp")
    print("step 15 done")
    if restaurants_added[0] == '`':
        restaurants_added = restaurants_added[7:]
        restaurants_added = restaurants_added[:-4]
    output_json = convert_string_to_json(restaurants_added)
    num_days = len(output_json['itinerary_with_restaurants'])
    fh.set_status(sessionid, "Almost there")
    temp_json = retry_until_success(get_itinerary_json, restaurants_added, attractions, chat_history,
                                    shortlisted_attractions, num_days)
    output_json = {}
    for i in temp_json:
        curr_val = {}
        if i is not None:
            if "complete_itinerary" in i:
                curr_val = i["complete_itinerary"]
            else:
                curr_val = i
        output_json = output_json | curr_val
    fh.set_status(sessionid, "Done")
    for day in output_json:
        for activity in output_json[day]:
            if activity['image_url'] is None:
                activity['image_url'] = bing_image_urls(activity['SightseeingName'], limit=10)
    return output_json














