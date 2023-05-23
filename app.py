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
    cipher = AES.new(config.KEY, AES.MODE_CBC, iv=config.IV)
    encrypted_auth = cipher.encrypt(pad(bytes(data["auth"], "utf-8"), AES.block_size))
    try:
        user = User(
            discord_id=data["discord_id"],
            basket=[],
            wii_id=data["wii_id"],
            auth_token=encode_hex_to_str(encrypted_auth),
            roo_uid=data["roo_uid"],
            auth_key="",
        )

        db.session.add(user)
        db.session.commit()
    except Exception as e:
        # Most likely the user already registered.
        query = User.query.filter_by(discord_id=data["discord_id"]).first()
        if not query:
            return Response(status=500)

        query.wii_id = data["wii_id"]
        query.auth_token = encode_hex_to_str(encrypted_auth)
        query.roo_uid = data["roo_uid"]
        db.session.add(query)
        db.session.commit()
        return "very good"

    return "very good"


@app.get("/tos")
def tos():
    return """
    Terms of Use
    <br>
    <br>
    These Terms of Use ("Terms") are a legal agreement between the WiiLink Team and
    its related affiliates ("us," "our," or "we") and you ("you", "your", or "users"). By using, visiting or
    browsing this website or WiiLink's Demae Domino's service, you accept and agree to be bound by these
    Terms of Use. If you do not agree to these Terms of Use, you should not use the Demae Domino's service
    or this website. These Terms of Use affect your rights, and you should read them carefully. The WiiLink Team
    reserves the right to remove and permanently delete Your Content from the Service with or without
    notice for any or no reason.
    <br>
    <br>
    Changes to Terms of Use
    <br>
    <br>
    The WiiLink Team reserves the right to update these Terms, which we may do for reasons that include,
    but are not limited to, complying with changes to the law or reflecting enhancements to the Service. If the
    changes affect your usage of the Service or your legal rights, we'll notify you no less than seven days
    before the changes take effect. Unless we state otherwise, your continued use of the Service after we post
    modifications will constitute your acceptance of and agreement to those changes.
    If you object to the changes, your recourse shall be to cease using the Service.
    <br>
    <br>
    What these terms apply to
    <br>
    <br>
    These Terms of Use apply to the Demae Deliveroo service. These Terms do not apply to our
    other services such as the <a href="https://wiilink24.com">WiiLink website</a>, Wii Room, Digicam Print Channel
    and the vanilla Demae Channel. For the Terms of Use for those services, please visit this
    <a href="https://www.wiilink24.com/eula.txt">link</a>
    <br>
    <br>
    Privacy and Personal Information
    <br>
    <br>
    By agreeing to these Terms of Use, you also agree to our <a href="/privacypolicy">Privacy Policy</a>.
    Please read them as they affect your rights.
    <br>
    <br>
    Demae Deliveroo Access
    <br>
    <br>
    WiiLink hereby grants you permission to use this website and Demae Domino's site as set forth in these
    Terms of Use, provided that: (i) your use of the service is for your own personal use, 
    (ii) you entered correct information into the Set Personal Data channel, (iii) you will otherwise comply 
    with the terms and conditions of these Terms of Use.
    <br>
    <br>
    You agree not to use or launch any automated system, including without limitation, "robots," "spiders,"
    "offline readers," etc., that accesses the Website or Applications in a manner that sends more request
    messages to the WiiLink servers in a given period of time than a human can reasonably produce in the
    same period by using the Demae Channel. You agree not to collect or harvest any personally identifiable
    information, including account names, from the Website or Applications, nor to use the communication
    systems provided by this website for any commercial solicitation purposes.
    <br>
    <br>
    Limitation of Liability
    <br>
    <br>
    In no event shall WiiLink be liable to you for any direct,
    indirect, incidental, special, punitive, or consequential damages whatsoever resulting from any (i) errors,
    mistakes, or inaccuracies of content, (ii) personal injury or property damage, of any nature whatsoever,
    resulting from your access to and use of our website or service, (iii) any unauthorized access to or
    use of our secure servers and/or any and all personal information and/or financial information stored therein,
    (iv) any interruption or cessation of transmission to or from our website or applications, (iv) any bugs,
    viruses, trojan horses, or the like, which may be transmitted to or through our website or service by
    any third party. The foregoing limitation of liability shall apply to the fullest extent permitted by law
    in the applicable jurisdiction.
    <br>
    <br>
    Ability To Accept Terms Of Use
    <br>
    <br>
    You affirm that you are 18 or more years of age. Deliveroo's terms of service state that you must be at least 18
    years of age to use their service. As such, we must follow that.
    <br>
    <br>
    You also affirm that you live in a region where Deliveroo is active. If you do not, you cannot
    use the Demae Deliveroo service.
    """


@app.get("/privacy_policy")
def privacy():
    return """
    Privacy Policy
    <br>
    <br>
    The protection and confidentiality of personal data something WiiLink takes extremely seriously. We
    believe in protecting the information accessed in the most secure way possible. We also believe that
    being transparent on how we access your data leads to a bigger sense of trust with the consumer.
    <br>
    <br>
    Please take your time and read through this Privacy Policy to the best of your ability to learn how
    we access and store your data. You will be notified through our Discord server if this document changes.
    <br>
    <br>
    This Privacy Policy only applies to the Demae Deliveroo service of WiiLink. For information on our other
    services, please read <a href="https://wiilink24.com/eula.txt">this</a>. By using the Demae Deliveroo
    service, you consent to our practices stated in this document. If you do not consent, please exit this
    page and do not use our services. Since this service utilizes the Deliveroo API, you are also
    required to agree to their <a href="https://deliveroo.co.uk/legal">Terms of Use and Privacy Policy</a>.
    <br>
    <br>
    If you do not live in a region Deliveroo supports, you are not authorized to
    use this service. Please exit this website and do not return.
    <br>
    <br>
    If you have any questions or concerns about this Privacy Policy, do not hesitate to reach out to staff
    in our Discord server.
    <br>
    <br>
    What do we access?
    <br>
    <br>
    In order to use the Demae Deliveroo service, you must use the Deliveroo Helper app found on our Github. This
    app assists in sending your auth token to our servers.
    Aside from this, there are other methods of data collection. Just by accessing this website,
    your IP address is being logged by our web server, nginx. 
    We access this data only in the following scenarios:
    <ul style="list-style-type: square">
    <li>Requesting nearby restaurants from Deliveroo</li>
    <li>Requesting the price of a basket from Deliveroo</li>
    <li>Placing an order to Deliveroo</li>
    </ul>
    <br>
    Children's Privacy
    <br>
    <br>
    This service is not intended for children under the age of 18. If you are under the age of 18, please exit
    this website and do not access this service. WiiLink does not knowingly collect data from children under
    the age of 13.
    <br>
    <br>
    Changes to this Privacy Policy
    <br>
    <br>
    It is our policy to inform the consumers to any changes to this privacy policy. If there is a change, you
    will be notified through our Discord server or News Server. The revision date of the privacy policy is
    at the bottom of the page.
    <br>
    <br>
    Last Modified
    <br>
    <br>
    Monday April 10th 2023
    """
