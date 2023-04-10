from flask import Flask, request, Response
import config
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from models import db, User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = config.secret_key

db.init_app(app)

ROO_VERSION = "3.109.0"

with open("login_steps.json", "r") as file:
    login_steps = json.loads(file.read())


@app.get("/steps")
def steps():
    i = len(login_steps["login"])
    i2 = len(login_steps["2fa"])
    return json.dumps({
        "login": i,
        "2fa": i2,
        "roo_ver": ROO_VERSION,
        "ua": f"Deliveroo/{ROO_VERSION} (samsung SM-G935F;Android 8.0.0;it-IT;releaseEnv release)"
    })


@app.get("/login")
def step_login():
    nStep = int(request.args.get("step"))
    step = login_steps["login"][nStep]
    return json.dumps({
        "status": True,
        "data": step
    })


@app.get("/mfa")
def step_2fa():
    nStep = int(request.args.get("step"))
    step = login_steps["2fa"][nStep]
    return json.dumps({
        "status": True,
        "data": step
    })


def encode_hex_to_str(array: bytes) -> str:
    hextable = "0123456789abcdef"
    ret = ""
    for b in array:
        ret += hextable[b >> 4]
        ret += hextable[b & 0x0f]

    return ret


@app.post("/receive")
def receive():
    data = json.loads(request.data)
    try:
        cipher = AES.new(config.KEY, AES.MODE_CBC, iv=config.IV)
        encrypted_auth = cipher.encrypt(pad(bytes(data["auth"], "utf-8"), AES.block_size))

        user = User(
            discord_id=data["discord_id"],
            basket=[],
            wii_id=data["wii_id"],
            auth_token=encode_hex_to_str(encrypted_auth),
            roo_uid=data["roo_uid"]
        )

        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(e.with_traceback(e.__traceback__))
        return Response(status=500)

    return "very good"
