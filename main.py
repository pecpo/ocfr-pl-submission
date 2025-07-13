from datetime import datetime
import threading

import tbo_general as tbo
import tbo_hotel_queries as hotels
from fastapi import FastAPI, Cookie, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import Response
from pydantic import BaseModel
from starlette.responses import RedirectResponse, JSONResponse
import sightseeing_llm_queries as llm
import services

import firebase_handler as fh
import geminiFunctions as gemini

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["set-cookie"]  # Explicitly expose the Set-Cookie header
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/updateNextAi")
async def updateNextAi(sessionid: str):
    history = fh.get_ai_chat(sessionid)
    if len(history) % 2 == 0:
        return -1
    response = gemini.next_message_for_ai_chat(history)
    fh.add_message_to_ai_chat("model", sessionid, response)
    return "ok"


@app.get("/getLLMDescription")
async def getLLMDescription(activityid: str, groupid: str):
    services.populateDescription(activityid, groupid)
    return "ok"


@app.get("/addCustomActivity")
async def addCustomActivity(groupid: str, name: str, cityname: str, fromdate: str, todate: str):
    activity = {}
    activity["Name"] = name
    activity["CityName"] = cityname
    activity["FromDate"] = fromdate
    activity["ToDate"] = todate
    activity["ImageList"] = []
    activity["Price"] = 0
    fh.add_activity_to_itinerary(groupid, activity)


@app.get("/updateNextInitial")
async def updateNextInitial(sessionid: str):
    history = fh.get_first_chat(sessionid)
    if len(history) % 2 == 0:
        return -1
    response = gemini.next_message_for_initial_chat(history)
    if ("Received hihihiha" in response):
        realhist = history.copy()
        history.append({"role": "model", "parts": [{"text": response}]})
        history.append({"role": "user", "parts": [{
            "text": "Sorry, just to recap things again, as I missed your last message, could you give me the summary again ?"}]})
        response = gemini.next_message_for_initial_chat(history)
        name = gemini.get_session_title(realhist)
        fh.add_group_name(name, sessionid)
        fh.add_summary(sessionid, response)
        realhist = realhist[0:-2]
        thread = threading.Thread(target=services.additinerary, args=(realhist, sessionid, True))
        thread.start()
        return {"status": "chat finished"}
    fh.add_message_to_first_chat("model", sessionid, response)
    return "ok"


@app.get("/addAiMessage")
async def addAiMessage(sessionid: str, message: str):
    history = fh.get_ai_chat(sessionid)
    if len(history) % 2 == 1:
        return -1
    fh.add_message_to_ai_chat("user", sessionid, message)
    return "ok"


@app.get("/addInitialMessage")
async def addInitialMessage(sessionid: str, message: str):
    history = fh.get_first_chat(sessionid)
    if len(history) % 2 == 1:
        return -1
    fh.add_message_to_first_chat("user", sessionid, message)
    return "ok"


@app.get("/addGroupMessage")
async def addGroupMessage(groupid: str, message: str, request: Request):
    idToken = request.cookies.get("session")
    userid = fh.get_uid(idToken)
    username = fh.get_name_by_userid(userid)
    fh.add_message_to_group_chat(username, groupid, message)
    if "@Tobey" in message:
        print(groupid)
        thread = threading.Thread(target=services.groupChatReturn, args=(groupid,))
        thread.start()
    return "ok"


@app.get("/addActivityToItinerary")
async def addActivityToItinerary(groupid: str, activityid: str, fromdate: str, todate: str):
    activity = fh.get_activity_by_id(groupid, activityid)
    activity = services.addTimeToActivity(activity, fromdate, todate)
    return fh.add_activity_to_itinerary(groupid, activity)


@app.get("/removeActivityFromItinerary")
async def addActivityToItinerary(groupid: str, activityid: str):
    fh.remove_activity_from_itinerary(groupid, activityid)


@app.get("/updateActivityInItinerary")
async def updateActivityInItinerary(groupid: str, activityid: str, fromdate: str, todate: str):
    a = fh.update_activity(groupid, activityid, fromdate, todate)
    if 'error' in a:
        return JSONResponse({'error': a}, status_code=400)


@app.get("/getAllActivities")
async def getAllActivities(groupid: str):
    return fh.get_all_activities(groupid)


@app.get("/createUser")
async def createUser(request: Request):
    idToken = request.cookies.get("session")
    print("token is", idToken)
    email = fh.get_email(idToken)
    userid = fh.get_uid(idToken)
    username = fh.get_name_by_session_cookie(idToken)
    fh.create_user(username, email, userid)
    return "ok"


@app.get("/createGroup")
async def createGroup(request: Request):
    idToken = request.cookies.get("session")
    userid = fh.get_uid(idToken)
    try:
        return {"groupId": fh.create_group(userid)}
    except Exception as e:
        print("oh boy", e)
        return {"groupId": None}


class AuthToken(BaseModel):
    idToken: str


@app.post("/authenticateUser")
async def authenticateUser(token: AuthToken):
    print("id token is", token.idToken)
    cookie = fh.verify_id_token(token.idToken)
    response = JSONResponse(content={"status": "ok"}, status_code=200)
    response.set_cookie(
        key="session",
        value=cookie,
        samesite="lax",
        secure=False,
        httponly=True,
        path="/"
    )
    return response


@app.get("/authenticateSession")
async def authenticateSession(request: Request):
    cookie = request.cookies.get("session")
    print("cookie is", cookie)
    return {"session": fh.verify_session_cookie(cookie)}


@app.get("/getGroups")
async def getGroups(request: Request):
    cookie = request.cookies.get("session")
    uid = fh.get_uid(cookie)
    a = fh.get_groups(uid)
    print(a)
    return a


@app.get("/getGroupName")
async def getGroupName(groupId: str):
    return {"name": fh.get_group_name(groupId)}


@app.get("/getGroupMemberCount")
async def getGroupMemberCount(groupId: str):
    return {"count": fh.get_group_member_count(groupId)}


@app.get("/leaveGroup")
async def leaveGroup(groupId: str, request: Request):
    cookie = request.cookies.get("session")
    userid = fh.get_uid(cookie)
    fh.group_leave(groupId, userid)
    return {"status": "ok"}


@app.get("/joinGroup")
async def joinGroup(groupId: str, request: Request):
    if fh.check_group_existance(groupId) is False:
        return {"status": "Group does not exist"}
    cookie = request.cookies.get("session")
    userid = fh.get_uid(cookie)
    fh.group_join(groupId, userid)

    return {"status": "ok"}


@app.get("/signOut")
async def signOut():
    response = JSONResponse(content={"status": "ok"}, status_code=200)
    response.set_cookie(
        key="session",
        value="",
        samesite="lax",
        secure=False,
        httponly=True,
        path="/",
        max_age=0
    )
    return response


@app.get("/updateBudget")
async def updateBudget(groupid: str, budget: float, request: Request):
    fh.update_budget(groupid, budget)


@app.get("/llmSearch")
async def llmSearch(groupid: str, query: str):
    activities = fh.get_all_activities_with_id(groupid)
    a = gemini.get_search_result(query, activities)
    return a


@app.get("/getCities")
async def getCities(groupid: str):
    cityIds = fh.get_city_ids(groupid)
    countryCode = fh.get_country_code(groupid)
    cityNames = []
    cities = tbo.get_city_list(countryCode)
    for cityId in cityIds:
        for city in cities:
            if city['Code'] == cityId:
                cityNames.append((city['Name'], cityId))
                break
    ans = {}
    for a in cityNames:
        r = hotels.get_hotels_list(a[1])
        if 'Hotels' in r:
            ans[a[0]] = r['Hotels']
    return ans
    # this will return a list of cities along with a list of all possible hotels for each city in this format:
    # {city name: {tbo json}, city 2 name: {tbo json}}


class RegenerateHotels(BaseModel):
    hotels: dict
    groupId: str


@app.post("/regenerateItinerary")
async def regenerateItinerary(selhotels: RegenerateHotels):
    print(selhotels.hotels)
    groupId = selhotels.groupId
    history = fh.get_first_chat(groupId)
    s = ""
    for k, v in selhotels.hotels.items():
        # k is city name v is hotel code
        if v == -1:
            s += k + ": not chosen\n"
        else:
            x = hotels.get_hotel_details(v)
            if 'Images' in x:
                x.pop('Images')
            s += k + ": " + str(x) + "\n"
    history[-1]['parts'][0][
        'text'] += "\nThis is the list of hotels that I have recieved from another llm, kindly choose hotels among these:\n" + s
    fh.set_status(groupId, "Preparing itinerary for regeneration")
    name = gemini.get_session_title(history)
    fh.add_group_name(name, groupId)
    thread = threading.Thread(target=services.additinerary, args=(history, groupId, False))
    thread.start()
    return

@app.get("/getHotelDetails")
def get_hotel_details(hotelCode: str):
    x = hotels.get_hotel_details(hotelCode)['HotelDetails']
    print(x[0])
    return x[0]

import hotel_llm_queries as hotelllm

@app.get("/getHotelLLMDescription")
def get_hotel_llm_description(hotelCode: str, groupId: str):
    hist = fh.get_first_chat(groupId)
    return hotelllm.get_hotel_description(hotelCode, hist)