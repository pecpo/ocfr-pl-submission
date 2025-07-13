from geminiFunctions import *
from prompts_and_sys_instructions import *
import pickle
def start_init_chat():
    system_instruction = system_instructions_for_initial_chat
    history, chat, _ = start_chat(system_instruction)
    history,chat = send_message("hi there", history, chat, system_instruction)
    while True:
        user_input = input("Enter your message: ")
        history, chat = send_message(user_input, history, chat, system_instruction)
        if ("Received hihihiha" in history[-1]["parts"][0]["text"]):
            break
    return history, chat

history,chat = start_init_chat()

with open("init_chat_history.txt", "w") as f:
    f.write(str(history))

with open("init_chat.pkl", "wb") as f:
    pickle.dump(chat, f)
