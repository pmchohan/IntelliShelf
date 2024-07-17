from fastapi import FastAPI
from neo import borrow_or_return
import uvicorn

app = FastAPI()
ops = 0
type = 'not-set'
name = 'not-set'
extra = 'not-set'
id = 'not-set'
book_id = 'not-set'
borrowed = False
loggedIn = False


@app.get("/")
async def read_root():
    global loggedIn, type, name, ops
    if not loggedIn:
        if type == 'book':
            ops = 1     # Login First
        elif type == 'student':
            loggedIn = True
            ops = 2     # Login Successful
            type = 'not-set'
    else:
        if type == 'student':
            ops = 3     # User already logged in
        elif type == 'book':
            if borrowed:
                ops = 4     # Book Borrowed
            else:
                ops = 8     # returned
    if ops == 6 or ops == 7:        # Register a new Book or Student
        return {"option": ops, 'name': name, 'type': type, 'extra': extra, 'id': id}
    return {"option": ops, 'name': name}


@app.post("/")
async def incoming(data: dict):
    print("Incoming data:", data)
    global type, name, extra, id, book_id, borrowed
    type = data['type'].strip()
    name = data['name'].strip()
    extra = data['extra'].strip()
    if type == 'student':
        id = data['id'].strip()
    elif type == 'book':
        book_id = data['id'].strip()
        borrowed = borrow_or_return(id, book_id)
    return "Success"


@app.get("/status")
async def get_status():
    return {'loggedIn': loggedIn, 'id': id}


@app.post("/status")
async def set_status(data: dict):
    global loggedIn, ops, type
    loggedIn = data['loggedIn']
    if not loggedIn:
        ops = 5
        type = 'not-set'
    return "Success"


@app.get("/reset")
async def reset():
    global loggedIn, type, name, ops
    loggedIn = False
    type = 'not-set'
    name = 'not-set'
    ops = 0
    return "Success"


@app.post("/set-op")
async def set_option(data: dict):
    global ops, type, name, extra, id
    ops = data['option']
    if ops == 6 or ops == 7:
        type = data['type']
        name = data['name']
        extra = data['extra']
        id = data['id']
    return "Success"


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", reload=True)
    print("Server started")
