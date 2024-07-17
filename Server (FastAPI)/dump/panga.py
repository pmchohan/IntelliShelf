import requests, time

url = 'http://192.168.2.3:8000/'

while True:
    try:
        response = requests.get(url+'get-t')
        if response.status_code == 200:
            type = response.json()['type']
            print("Type:", type)
            r = requests.get(url+'get-l')
            if r.status_code == 200:
                loggedIn = r.json()['logged']
                if loggedIn == "false":
                    if type == 'book':
                        r = requests.post(url+'set-op', json={'option': 1})
                        if r.status_code != 200:
                            print("POST /set-op Error")
                    if type == 'student':
                        r = requests.post(url+'set-l', json={'logged': 'true'})
                        if r.status_code != 200:
                            print("POST /set-l Error")
                        r = requests.post(url+'set-op', json={'option': 2})
                        if r.status_code != 200:
                            print("POST /set-op Error")
                        r = requests.post(url+'set-t', json={'type': 'not-set'})
                        if r.status_code != 200:
                            print("POST /set-t Error")
                else:
                    if type == 'student':
                        r = requests.post(url+'set-op', json={'option': 3})
                        if r.status_code != 200:
                            print("POST /set-op Error")
                    elif type == 'book':
                        r = requests.post(url+'set-op', json={'option': 4})
                        if r.status_code != 200:
                            print("POST /set-op Error")
            else:
                print("GET /get-l Error")
        else:
            print("POST /get-t Error")
    except requests.exceptions.ConnectionError as e:
        print("Connection error:", e)
        time.sleep(1)
    time.sleep(1)
