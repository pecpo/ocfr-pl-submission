import sightseeing_llm_queries as llm
import firebase_handler as fh
import geminiFunctions as gemini

def convertLlmActivityToActivity(llm_activity):
    ans = {}
    ans["Name"] = llm_activity["SightseeingName"]
    ans['Price'] = llm_activity["price"]
    ans['Currency'] = llm_activity['currency']
    ans['ImageList'] = llm_activity["image_url"]
    ans['FromDate'] = llm_activity["FromDate"]
    ans['ToDate'] = llm_activity["ToDate"]
    ans['tbo_description'] = llm_activity["tbo_description"]
    ans['llm_description'] = llm_activity["llm_description"]
    ans['rating'] = llm_activity["ai_rating"]
    ans["CityName"] = llm_activity["city_name"]
    return ans


def convert_llm_itinerary(llm_itinerary):
    ans = []
    for k, v in llm_itinerary.items():
        for curr in v:
            ans.append(convertLlmActivityToActivity(curr))
    return ans


def convertTboToActivity(tbo_activity):
    ans = {}
    ans["Name"] = tbo_activity["SightseeingName"]
    ans["CityName"] = tbo_activity["CityName"]
    ans['ImageList'] = tbo_activity["ImageList"]
    ans['Price'] = tbo_activity["Price"]['OfferedPriceRoundedOff']
    ans['Currency'] = tbo_activity["Price"]['CurrencyCode']
    return ans


def convertTboToActivities(tbo_activities):
    ans = []
    for curr in tbo_activities:
        if curr['Response']['SightseeingSearchResults'] is not None:
            for activity in curr['Response']['SightseeingSearchResults']:
                if activity is not None:
                    ans.append(convertTboToActivity(activity))
    return ans


def additinerary(hist, sessionid, e):
    fh.restore_session(sessionid)
    final = llm.get_itinerary_after_chat(hist, sessionid, e)
    final = convert_llm_itinerary(final)
    budget = gemini.get_session_budget(hist)
    fh.update_budget(sessionid, budget)
    for activity in final:
        fh.add_activity_to_itinerary(sessionid, activity)

def populateDescription(activityid, groupid):
    history = fh.get_group_chat(groupid)
    history = convertGroupChatToLLMParseable(history)
    itinerary = fh.get_full_itinerary(groupid)
    activity = fh.get_activity_by_id(groupid, activityid)
    if activity is not None:
        fh.add_llm_description(groupid, activityid, gemini.get_attraction_llm_description(activity, itinerary, history))
    else:
        activity = fh.get_activity_by_id_in_itinerary(groupid, activityid)
        if activity is not None:
            print("hmmm, no activity must be an itinerary then")
            fh.add_llm_description_on_itinerary(groupid, activityid, gemini.get_attraction_llm_description(activity, itinerary, history))

def addAllAttractions(attractions, sessionid):
    ans = convertTboToActivities(attractions)
    fh.add_activities(sessionid, ans)
    print("added attractions")


def addTimeToActivity(activity, fromdate, todate):
    activity['FromDate'] = fromdate
    activity['ToDate'] = todate
    return activity


def convertGroupChatToLLMParseable(groupchat):
    llmchat = []
    las = {}
    for message in groupchat:
        if message['user'] == 'Tobey':
            llmchat.append(las)
            las['role'] = 'model'
            las['parts'] = [{'text': message['message']}]
        else:
            try:
                if las['role'] == 'user':
                    las['parts'] = [{'text': las['parts'][0]['text'] + "\n" + message['message']}]
                    continue
            except:
                pass
            las['role'] = 'user'
            las['parts'] = [{'text': message['message']}]
    if las != {}:
        llmchat.append(las)
    while (len(llmchat) and llmchat[-1]['role'] == 'model'):
        llmchat = llmchat[0:-2]
    return llmchat

def groupChatReturn(groupid):
    print("Someone has summoned Tobey")
    groupchat = fh.get_group_chat(groupid)
    groupchat = convertGroupChatToLLMParseable(groupchat)
    itinerary = fh.get_full_itinerary(groupid)
    attractions = fh.get_all_activities_with_id(groupid)
    message = gemini.next_message_for_ai_chat(groupchat, itinerary, attractions)
    fh.add_message_to_group_chat('Tobey', groupid, message)
