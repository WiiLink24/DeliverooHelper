import base64
import json
import os
import uuid

import colorama
import requests
import string
import random
import textwrap
from colorama import Fore, Style

colorama.init()
r = requests.session()
user_data = {}


def clear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


console_width = os.get_terminal_size().columns

ROO_HEADER = {
    "Accept-Language": "en-UK",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept-Encoding": "gzip",
    "X-Roo-Country": "uk"
}


def main():
    clear()
    print("WiiLink Deliveroo Login Helper - (c) 2023 WiiLink")
    print(("=" * console_width) + "\n")
    print(
        Fore.LIGHTGREEN_EX + textwrap.fill("NOTE: If you have any issues with this program, please make a support "
                                           "ticket in the WiiLink Discord Server: https://discord.gg/WiiLink",
                                           console_width) + Style.RESET_ALL + "\n")

    val = input("1. Start\n2. Exit\n")
    if val == "1":
        actual_work()
    elif val == "2":
        exit(0)
    else:
        main()


def actual_work():
    clear()
    print("WiiLink Deliveroo Login Helper - (c) 2023 WiiLink")
    print(("=" * console_width) + "\n")
    print("Obtaining login steps from server...")

    response = requests.get("/steps")
    x = json.loads(response.text)
    num_of_steps = x["login"]
    _2fa_steps = x["2fa"]
    roo_ver = x["roo_ver"]
    ROO_HEADER.update({"User-Agent": x["ua"]})

    roo_uid = str(uuid.uuid4())
    idfv = id_generator(16, "1234567890abcdef")
    idfa = str(uuid.uuid4())
    ROO_HEADER.update({
        "X-Roo-Guid": roo_uid,
        "X-Roo-Sticky-Guid": roo_uid
    })
    user_obj = {
        "roo_uid": roo_uid,
        "idfv": idfv,
        "idfa": idfa
    }
    dev_prop = {
        "App Namespace": "com.deliveroo.orderapp",
        "App Version": roo_ver,
        "Platform": "Android",
        "OS Version": "8.0.0",
        "Device Model": "samsung SM-G935F",
        "Device Type": "Phone",
        "Locale": "en_UK",
        "IDFV": idfv,
        "IDFA": idfa,
        "Google Pay Status": "unknown",
        "Device Locale": "en_UK",
        "Device Language": "en-UK",
        "mvt_mfa_high_risk_login_android": "feature"
    }

    dev_data = base64.b64encode(bytes(json.dumps(dev_prop), "utf-8")).decode()
    r.cookies.set("roo_guid", roo_uid, domain="api.deliveroo.com", path="/")
    r.cookies.set("roo_super_properties", dev_data, domain="api.deliveroo.com", path="/")
    user_data.update({
        "roo_uid": roo_uid
    })

    print("Starting login flow...")
    for step in range(num_of_steps):
        response = requests.get("/login", params={"step": step})
        x = json.loads(response.text)
        if x["status"]:
            if x["data"]["method"] == 0:
                g = doGET(x["data"]["url"])

            elif x["data"]["method"] == 1:
                g = doPOST(x["data"], _2fa_steps)

            if x["data"]["check_code"] is not None:
                if g.status_code != x["data"]["check_code"]:
                    l = x["data"]["check_code"]
                    error(f"Got {g.status_code} instead of {l}. Response: {g.text}")
        else:
            error("The server experienced an error.")


def error(err):
    clear()
    print("WiiLink Deliveroo Login Helper - (c) 2023 WiiLink")
    print(("=" * console_width) + "\n")

    print(Fore.LIGHTRED_EX + textwrap.fill("An error has occurred during login. Please open a support thread in the "
                                           "WiiLink Discord server and send this screen.", console_width) +
          Style.RESET_ALL + "\n\n")

    print(f"Error: {err}")
    exit(0)

def doGET(url):
    p = url.split("?")[0]
    response = r.get(url, headers=ROO_HEADER, verify=True)
    return response

def doPOST(stepData, steps2fa):
    p = stepData["url"].split("?")[0]

    if stepData["type"] == "hd":
        response = r.post(stepData["url"], data=stepData["data"], headers=ROO_HEADER, verify=True)
        return response
    elif stepData["type"] == "ec":
        global email
        em = input(stepData["msg"])
        response = r.post(stepData["url"], data=json.dumps({stepData["field"]: em}), headers=ROO_HEADER, verify=True)
        x = json.loads(response.text)
        if not x["registered"]:
            error("Account not found.")
            exit()
        else:
            email = em
            return response
    elif stepData["type"] == "lo":
        ps = input(stepData["msg"])
        global auth
        auther = base64.b64encode(bytes(f"{email}:{ps}", "utf-8")).decode()
        auth = auther
        ROO_HEADER.update({
            "Authorization": f"Basic {auther}",
            "X-Roo-Challenge-Support": "passcode"
        })
        response = r.post(stepData["url"], data=stepData["data"], headers=ROO_HEADER, verify=True)
        if response.status_code == 423:
            print("Email and Password valid...")
            discord_id = input("Please enter your Discord ID => ")

            # There isn't much validation I can do without calling Discord's API. If they enter an invalid one it is
            # their loss anyway.
            if len(discord_id) < 17:
                error("Invalid Discord ID")
            try:
                int(discord_id)
            except ValueError:
                error("Invalid Discord ID")

            wii_id = input("Please enter your Wii ID => ")
            user_data.update({"discord_id": discord_id, "wii_id": wii_id})

            print("2FA is required...")
            mfa = json.loads(response.text)["mfa_token"]
            doMFA(steps2fa, mfa)
        elif response.status_code == 200 or response.status_code == 201:
            print("Email and Password valid...")
            discord_id = input("Please enter your Discord ID => ")

            # There isn't much validation I can do without calling Discord's API. If they enter an invalid one it is
            # their loss anyway.
            if len(discord_id) < 17:
                error("Invalid Discord ID")
            try:
                int(discord_id)
            except ValueError:
                error("Invalid Discord ID")

            wii_id = input("Please enter your Wii ID => ")
            user_data.update({"discord_id": discord_id, "wii_id": wii_id})


            #send data
            s = json.loads(response.text)
            userid = str(s["id"])
            sestk = s["session_token"]
            auth_str = f"{userid}:orderapp_android,{sestk}"
            auth64 = base64.b64encode(bytes(auth_str, "utf-8")).decode()
            auth = f"Basic {auth64}"
            sesID = r.cookies.get_dict()["roo_session_guid"]
            superProp = r.cookies.get_dict()["roo_super_properties"]
            user_data.update({
                "roo_session_guid": sesID,
                "roo_super_properties": superProp,
                "auth": auth
            })
            sendData()
        else:
            error(f"POST failed. Status code: {response.status_code}")
            exit()


def doMFA(steps, mfa):
    for step in range(steps):
        response = requests.get("/mfa", params={"step": step})
        x = json.loads(response.text)
        if x["status"]:
            stepData = x["data"]
            if stepData["type"] == "ss":
                data = {
                    "challenge": "sms:passcode",
                    "mfa_token": mfa,
                    "trigger": "send"
                }
                response = r.post(stepData["url"], data=json.dumps(data), headers=ROO_HEADER, verify=True)
                if response.status_code != stepData["check_code"]:
                    error("Send SMS failed.")
                else:
                    print("OTP was sent, please check your phone.")
            if stepData["type"] == "sc":
                c = input(stepData["msg"])
                data = {
                    "challenge": "sms:passcode",
                    "client_type": "orderapp_android",
                    "data":{
                            "passcode": str(c)
                    },
                    "mfa_token": mfa
                }
                response = r.post(stepData["url"], data=json.dumps(data), headers=ROO_HEADER, verify=True)
                if response.status_code != stepData["check_code"]:
                    error("OTP failed or was incorrect.")
                else:
                    # Send data to server
                    s = json.loads(response.text)
                    userid = str(s["id"])
                    sestk = s["session_token"]
                    auth_str = f"{userid}:orderapp_android,{sestk}"
                    auth64 = base64.b64encode(bytes(auth_str, "utf-8")).decode()
                    auth = f"Basic {auth64}"
                    sesID = r.cookies.get_dict()["roo_session_guid"]
                    superProp = r.cookies.get_dict()["roo_super_properties"]
                    user_data.update({
                        "roo_session_guid": sesID,
                        "roo_super_properties": superProp,
                        "auth": auth
                    })
                    sendData()

def sendData():
    res = requests.post("/receive", data=json.dumps(user_data))
    if res.status_code == 500:
        error("A database error has occurred")

    finish()

def finish():
    clear()
    print("WiiLink Deliveroo Login Helper - (c) 2023 WiiLink")
    print(("=" * console_width) + "\n")
    print("Successfully linked account. Please continue following the guide.")
    exit(0)

if __name__ == "__main__":
    main()
