from asyncio.windows_events import NULL
from cgi import print_environ
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "*"
]


class Registor_form(BaseModel):
    username: str
    password: str
    name: str
    surname: str
    telephone: str
    house_no: str
    village_no: str
    lane: str
    road: str
    sub_district: str
    district: str
    province: str
    postal_code: str
    serial: str


class Sensor(BaseModel):
    water_level: int
    gas: int
    smoke: int
    flame: int
    shake: int


class Token(BaseModel):
    access_token: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    name: str


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

client = MongoClient('mongodb://localhost', 27018)
db = client["Project"]
db_addr = db["Address"]
db_home = db["Home"]
db_user = db["User"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "d33c5f6a1d781b26efa06929e263dfe775a6c0c7bfca20dba36b4db26bbff00d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(dbx, username: str):
    if username in dbx:
        user_dict = dbx[username]
        # print("check")
        # print(dbx[username])
        return UserInDB(**user_dict)


def get_user_from_db():
    result = db_user.find({}, {"_id": 0})
    # print(result)
    dic = {}
    for r in result:
        dic[r['username']] = r
    return dic


def get_current_user(token: str = Depends(oauth2_scheme)):
    # print(db_user)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    db_userxxx = get_user_from_db()

    user = get_user(db_userxxx, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


@app.get("/")
def start():
    return {"status": "OK"}


@app.post("/register")
def reg(reg_form: Registor_form):
    form = jsonable_encoder(reg_form)
    query = {"username": form["username"]}
    res = db_user.find_one(query, {"_id": 0})
    res_s = db_home.find_one({"serial": form["serial"]},{"_id": 0})
    if res != None:
        # return {"result": "This username has been used"}
        raise HTTPException(400, "This username has been used")
    elif res_s != None:
        raise HTTPException(400, "This serial has been used")
    else:
        init_user = {
        "username": form["username"],
        "hashed_password": get_password_hash(form["password"]),
        "name": form["name"],
        "surname": form["surname"],
        "telephone": form["telephone"]
        }
        init_home = {
            "username": form["username"],
            "serial": form["serial"],
            "water_level": 0,
            "gas": 0,
            "smoke": 0,
            "flame": 0,
            "shake": 0,
        }
        init_addr = {
            "username": form["username"],
            "house_no": form["house_no"],
            "village_no": form["village_no"],
            "lane": form["lane"],
            "road": form["road"],
            "sub_district": form["sub_district"],
            "district": form["district"],
            "province": form["province"],
            "postal_code": form["postal_code"]
        }
        db_user.insert_one(init_user)
        db_home.insert_one(init_home)
        db_addr.insert_one(init_addr)
        # return {"result": "user has been added"}
        raise HTTPException(201, "User has been register")


@app.put("/update_sensor/{serial}")
def update_sensor(sensor: Sensor, serial: str):
    s = jsonable_encoder(sensor)
    # access_token = s["access_token"]
    # token_decoded = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256'])
    query = {"serial": serial}
    db_home.update_one(query, {"$set": {"water_level": s["water_level"],
                                        "gas": s["gas"],
                                        "smoke": s["smoke"],
                                        "flame": s["flame"],
                                        "shake": s["shake"]}})
    # return {"result": "Update success"}
    raise HTTPException(200, "Success change")


@app.get("/hard_get/{serial}")
def hard_get(serial: str):
    query = {"serial": serial}
    res = db_home.find_one(query, {"_id": 0})
    return res


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    users_db = get_user_from_db()
    user = authenticate_user(users_db, form_data.username, form_data.password)
    # print(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/get_sensor")
def get_sensor(current_user: User = Depends(get_current_user)):
    query = {"username": current_user.username}
    res = db_home.find_one(query, {"_id": 0})
    return {"result": res}


@app.get("/get_address")
def get_sensor(current_user: User = Depends(get_current_user)):
    query = {"username": current_user.username}
    res = db_addr.find_one(query, {"_id": 0})
    return {"result": res}
