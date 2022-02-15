from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import hashlib
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets
from typing import Optional


class Registor_form(BaseModel):
    username: str
    password: str
    name: str
    surname: str
    telephone: str
    house_no: str
    village_no: str
    alley: str
    lane: str
    road: str
    sub_district: str
    sub_area: str
    district: str
    province: str
    postal_code: str


class Sensor(BaseModel):
    water_level: float
    gas: float
    smoke: float
    flame: float
    shake: float
    wind: float


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


client = MongoClient('mongodb://localhost', 27018)
db = client["Project"]
db_addr = db["Address"]
db_home = db["Home"]
db_user = db["User"]

app = FastAPI()


@app.get("/")
def start():
    # return {"status": "OK"}
    raise HTTPException(200, "Success")


@app.post("/register")
def reg(reg_form: Registor_form):
    form = jsonable_encoder(reg_form)
    query = {"username": form["username"]}
    res = db_user.find(query, {"_id": 0})
    if len(list(res)) != 0:
        # return {"result": "This username has been used"}
        raise HTTPException(400, "This username has been used")
    else:
        init_user = {
            "username": form["username"],
            "password": hashlib.sha256(form["password"].encode()).hexdigest(),
            "name": form["name"],
            "surname": form["surname"],
            "telephone": form["telephone"]
        }
        init_home = {
            "username": form["username"],
            "water_level": 0,
            "gas": 0,
            "smoke": 0,
            "flame": 0,
            "shake": 0,
            "wind": 0
        }
        init_addr = {
            "username": form["username"],
            "house_no": form["house_no"],
            "village_no": form["village_no"],
            "alley": form["alley"],
            "lane": form["lane"],
            "road": form["road"],
            "sub_district": form["sub_district"],
            "sub_area": form["sub_area"],
            "district": form["district"],
            "province": form["province"],
            "postal_code": form["postal_code"]
        }
        db_user.insert_one(init_user)
        db_home.insert_one(init_home)
        db_addr.insert_one(init_addr)
        # return {"result": "user has been added"}
        raise HTTPException(201, "User has been register")


@app.put("/update_sensor/{username}")
def update_sensor(sensor: Sensor, username: str):
    s = jsonable_encoder(sensor)
    query = {"username": username}
    res = db_home.update_one(query, {"$set": {"water_level": s["water_level"],
                                              "gas": s["gas"],
                                              "smoke": s["smoke"],
                                              "flame": s["flame"],
                                              "shake": s["shake"],
                                              "wind": s["wind"]}})
    # return {"result": "Update success"}
    raise HTTPException(200, "Success change")


SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/check")
def check_pass(login: Login):
    l = jsonable_encoder(login)
    query = {"username": l["username"]}
    res = db_user.find_one(query)
    if res == None:
        return {"result": "Invalid username or password"}
    hash_input_pass = hashlib.sha256(l["password"].encode()).hexdigest()
    if hash_input_pass == res["password"]:
        access_token = create_access_token(data={"sub": l["username"]})
        print(access_token)
        return {"result": True,"access_token": access_token}
    if hash_input_pass == res["password"] :
        return {"result": True}
        # raise HTTPException(202, True)
    else:
        return {"result": False}
        # raise HTTPException(400, False)