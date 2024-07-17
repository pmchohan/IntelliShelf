import time,requests, streamlit as st
from chat import chat_response, newNode, create_episode, end_episode

loggedIn = None
user_id = 'not-set'
url = "http://192.168.70.3:8000/"

def checkStatus(delay: bool = True):
    global loggedIn, user_id
    # while True:
    if delay:
        time.sleep(0.2)
    r = requests.get(url+"status")
    if r.status_code != 200:
        print("GET /status Problem")
    else:
        loggedIn = r.json()['loggedIn']
        user_id =  r.json()['id']
checkStatus()

def typewriter(text, delay=0.1):
    for word in text.split():
        yield word + " "
        time.sleep(delay)
        
chat, register, add = st.tabs(["IntelliShelf 🧠", "Register a Student", "Add a book"])


with register:
    type = "student".ljust(16)
    with st.form("RegisterStudent", clear_on_submit=True, border=False):
        name = st.text_input("Name", max_chars=16, key=1).ljust(16).title()
        dept = st.text_input("Department", max_chars=16, key=2).ljust(16).upper()
        stid = st.text_input("Reg ID", max_chars=16, key=3).ljust(16).title()
        submitted = st.form_submit_button("Register This Student")
        if submitted:
            data = {'option':6, 'type': type, 'name': name, 'extra': dept, 'id': stid}
            newNode(type, name, dept, stid)
            r = requests.post(url+"set-op", json=data)


with add:
    type = "book".ljust(16)
    with st.form("AddBook", clear_on_submit=True, border=False):
        name = st.text_input("Name", max_chars=16, key=4, ).ljust(16).title()
        author = st.text_input("Author", max_chars=16, key=5).ljust(16).title()
        bid = st.text_input("Book ID", max_chars=16, key=6).ljust(16).title()
        submitted = st.form_submit_button("Add this Book")
        if submitted:
            data = {'option':7, 'type': type, 'name': name, 'extra': author, 'id': bid}
            newNode(type, name, author, bid)
            requests.post(url+"set-op", json=data)


with chat:
    st.title("Communicate with IntelliShelf 🤖")
    cont = st.container(height=430, border=True)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if loggedIn:
        # prompt = st.chat_input("Drop Your Thoughts here")
        # if prompt:
        if prompt := st.chat_input("Drop Your Thoughts here"):
            checkStatus(False)
            if not loggedIn:
                st.rerun()
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            reply = chat_response(prompt, user_id)
            
            for message in st.session_state.messages:
                with cont.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt.lower().strip() == "logout":
                cont.chat_message("assistant").write("Bye!!!")
                r = requests.post(url+"status", json={'loggedIn': False})
                if r.status_code != 200:
                    print("POST /status Problem")
                if "messages" in st.session_state:
                    st.session_state.messages = []
                end_episode(user_id)
                st.rerun()
            else:
                with st.spinner("visiting moon to get you a reply..."):
                    cont.chat_message("assistant").write_stream(typewriter(reply))

            st.session_state.messages.append({"role": "assistant", "content": reply})
            
    if not loggedIn:
        st.subheader("Scan your Card to Log In")
        while True:
            checkStatus()
            if loggedIn:
                create_episode(user_id)
                time.sleep(0.1)
                print(user_id)
                st.rerun()
