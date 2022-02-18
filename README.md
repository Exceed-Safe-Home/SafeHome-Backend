# SafeHome-Backend

## 📦 Build Steps

### 1. Setting up

```bash
$ git clone git@github.com:Exceed-Safe-Home/SafeHome-Backend.git
$ pip install -r requirements.txt
```

### 2. Serve (Mongodb)

```bash
$ ssh std07@10.3.134.191 -L 1234:localhost:1234 -L 27017:localhost:27017
password : up-to-each-admin
$ uvicorn main_project:app --port=8000 --reload
```