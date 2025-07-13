import firebase_admin
from firebase_admin import credentials, firestore, auth
import time
from datetime import datetime
import geminiFunctions as gemini

import services


def current_milli_time():
    return str(round(time.time() * 1000))


cred = credentials.Certificate("firebase_creds.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()
users_ref = db.collection("users")
sessions_ref = db.collection("sessions")


def create_user(name, email, userid):
    for doc in users_ref.get():
        if userid == doc.id:
            return
    users_ref.document(userid).set({'name': name, 'email': email, 'sessions': []})

def create_group(userid):
    ssid = current_milli_time()
    a = users_ref.document(userid).get().to_dict()['sessions']
    a.append(ssid)
    users_ref.document(userid).update({'sessions': a})
    a = [userid]
    sessions_ref.document(ssid).set({'users': a, 'owner': userid, 'status': 'Chatting'})
    print("returning: ", ssid)
    add_message_to_first_chat('user', ssid, "Hi there")
    hist = get_first_chat(ssid)
    response = gemini.next_message_for_initial_chat(hist)
    add_message_to_first_chat("model", ssid, response)
    return ssid


def add_message_to_first_chat(role, sessionid, message):
    sessions_ref.document(sessionid).collection("first chat").document(current_milli_time()).set(
        {'role': role, 'parts': [{'text': message}]})


def get_group_chat(sessionid):
    docs = sessions_ref.document(sessionid).collection("group chat").stream()
    arr = []
    for doc in docs:
        arr.append(doc.to_dict())
    return arr


def add_llm_description(sessionid, activityid, description):
    sessions_ref.document(sessionid).collection("activities").document(activityid).update(
        {'llmDescription': description})


def add_llm_description_on_itinerary(sessionid, activityid, description):
    sessions_ref.document(sessionid).collection("itinerary").document(activityid).update(
        {'llmDescription': description})


def get_first_chat(sessionid):
    docs = sessions_ref.document(sessionid).collection("first chat").stream()
    arr = []
    for doc in docs:
        arr.append(doc.to_dict())
    return arr


def get_ai_chat(sessionid):
    docs = sessions_ref.document(sessionid).collection("ai chat").stream()
    arr = []
    for doc in docs:
        arr.append(doc.to_dict())
    return arr


def add_message_to_group_chat(username, sessionid, message):
    sessions_ref.document(sessionid).collection("group chat").document(current_milli_time()).set(
        {'message': message, 'user': username})


def add_message_to_ai_chat(role, sessionid, message):
    sessions_ref.document(sessionid).collection("ai chat").document(current_milli_time()).set(
        {'role': role, 'parts': [{'text': message}]})


def add_activities(sessionid, activities):
    for activity in activities:
        print("adding smth")
        sessions_ref.document(sessionid).collection("activities").document(current_milli_time()).set(activity)


def add_activity_to_itinerary(sessionid, activity):
    # Convert string dates to datetime objects for comparison
    new_start = datetime.fromisoformat(activity['FromDate'].replace('Z', '+00:00'))
    new_end = datetime.fromisoformat(activity['ToDate'].replace('Z', '+00:00'))

    # Get all existing activities for the day
    itinerary_ref = sessions_ref.document(sessionid).collection("itinerary")
    existing_activities = itinerary_ref.get()

    # Check for overlaps
    for existing in existing_activities:
        data = existing.to_dict()
        if 'FromDate' not in data or 'ToDate' not in data:
            continue

        existing_start = datetime.fromisoformat(data['FromDate'].replace('Z', '+00:00'))
        existing_end = datetime.fromisoformat(data['ToDate'].replace('Z', '+00:00'))

        # Check if activities overlap
        if (new_start < existing_end and new_end > existing_start):
            return -1

    # If no overlaps, add the activity
    id = str(current_milli_time())
    print(id)
    itinerary_ref.document(id).set(activity)
    return id


def remove_activity_from_itinerary(sessionid, activity):
    sessions_ref.document(sessionid).collection("itinerary").document(activity).delete()


def update_activity(sessionid, activityid, fromdate, todate):
    session_ref = sessions_ref.document(sessionid)

    # Convert string dates to datetime objects for comparison
    new_start = datetime.fromisoformat(fromdate.replace('Z', '+00:00'))
    new_end = datetime.fromisoformat(todate.replace('Z', '+00:00'))

    # Validate time range
    if new_start >= new_end:
        return {"error": "Invalid time range: start time must be before end time"}

    # Get all activities for this day to check for overlaps
    itinerary_ref = session_ref.collection("itinerary")
    activities = itinerary_ref.get()

    # Check for overlaps with other activities
    for activity in activities:
        # Skip the current activity being updated
        if activity.id == activityid:
            continue

        activity_data = activity.to_dict()
        existing_start = datetime.fromisoformat(activity_data['FromDate'].replace('Z', '+00:00'))
        existing_end = datetime.fromisoformat(activity_data['ToDate'].replace('Z', '+00:00'))

        # Check if activities overlap
        if (
                (new_start < existing_end and new_end > existing_start) or
                (new_start < existing_start and new_end > existing_end)
        ):
            return {
                "error": "Time slot occupied",
                "description": "This time slot overlaps with an existing activity"
            }

    # If no overlaps, update the activity
    try:
        itinerary_ref.document(activityid).update({
            'FromDate': fromdate,
            'ToDate': todate
        })
        return {"success": True}
    except Exception as e:
        return {"error": f"Failed to update activity: {str(e)}"}


def set_status(sessionid, status):
    sessions_ref.document(sessionid).update({'status': status})


def get_full_itinerary(sessionid):
    arr = []
    docs = sessions_ref.document(sessionid).collection("itinerary").stream()
    for doc in docs:
        arr.append(doc.to_dict())
    return arr


def get_name_by_userid(userid):
    return users_ref.document(userid).get().to_dict()['name']


def get_activity_by_id(sessionid, activityid):
    return sessions_ref.document(sessionid).collection("activities").document(activityid).get().to_dict()


def get_activity_by_id_in_itinerary(sessionid, activityid):
    return sessions_ref.document(sessionid).collection("itinerary").document(activityid).get().to_dict()


def get_all_activities(sessionid):
    arr = []
    docs = sessions_ref.document(sessionid).collection("activities").stream()
    for doc in docs:
        arr.append([doc.id, doc.to_dict()])
    return arr


def add_summary(sessionid, summary):
    sessions_ref.document(sessionid).update({"summary": summary})


def get_summary(sessionid):
    return sessions_ref.document(sessionid).get().to_dict()['summary']


def verify_id_token(idToken):
    print(auth.verify_id_token(idToken))
    return auth.create_session_cookie(idToken, 60 * 60 * 24 * 5)


def verify_session_cookie(cookie):
    try:
        print(auth.verify_session_cookie(cookie))
        return True
    except:
        return False


def get_uid(idToken):
    return auth.verify_session_cookie(idToken)['uid']


def get_email(idToken):
    return auth.verify_session_cookie(idToken)['email']


def get_name_by_session_cookie(idToken):
    return auth.verify_session_cookie(idToken)['name']


def get_groups(userid):
    a = users_ref.document(userid).get().to_dict()['sessions']
    temp = a.copy()
    for c in a:
        if check_group_existance(c) == False:
            temp.remove(c)
    a = temp
    r = []
    for c in a:
        x = sessions_ref.document(c).get().to_dict()
        name='Untitled group'
        if ('name' in x.keys()):
            name = x['name']
        r.append({'name': name, 'member count': len(x['users']), 'id': c})
    return r


def get_group_name(groupId):
    try:
        a = sessions_ref.document(groupId).get().to_dict()['name']
        return a
    except:
        return "Untitled group"


def get_group_member_count(groupId):
    a = sessions_ref.document(groupId).get().to_dict()['users']
    return len(a)


def group_leave(groupId, userid):
    arr = users_ref.document(userid).get().to_dict()['sessions']
    arr.remove(groupId)
    users_ref.document(userid).update({'sessions': arr})
    arr = sessions_ref.document(groupId).get().to_dict()['users']
    arr.remove(userid)
    sessions_ref.document(groupId).update({'users': arr})


def group_join(groupId, userid):
    a = users_ref.document(userid).get().to_dict()['sessions']
    a.append(groupId)
    users_ref.document(userid).update({'sessions': a})
    # Added to user now adding to group
    a = sessions_ref.document(groupId).get().to_dict()['users']
    a.append(userid)
    sessions_ref.document(groupId).update({'users': a})


def check_group_existance(groupId):
    return sessions_ref.document(groupId).get().exists


def update_budget(groupid, budget):
    sessions_ref.document(groupid).update({'budget': budget})


def get_all_activities_with_id(groupid):
    arr = []
    docs = sessions_ref.document(groupid).collection("activities").stream()
    for doc in docs:
        curr = doc.to_dict()
        curr['id'] = doc.id
        arr.append(curr)
    return arr


def add_group_name(name, sessionid):
    sessions_ref.document(sessionid).update({'name': name})

#TODO: set city ids in createitinerary function
def set_city_ids(sessionid, cityId):
    sessions_ref.document(sessionid).update({'cities': cityId})

def get_city_ids(sessionid):
    return sessions_ref.document(sessionid).get().to_dict()['cities']

def restore_session(sessionid):
    try:
        docs = sessions_ref.document(sessionid).collection("activities").stream()
        for doc in docs:
            sessions_ref.document(sessionid).collection("activities").document(doc.id).delete()
        docs = sessions_ref.document(sessionid).collection("itinerary").stream()
        for doc in docs:
            sessions_ref.document(sessionid).collection("itinerary").document(doc.id).delete()
    except:
        pass


def set_country_code(sessionid, countryCode):
    sessions_ref.document(sessionid).update({'countryCode': countryCode})

def get_country_code(sessionid):
    return sessions_ref.document(sessionid).get().to_dict()['countryCode']
