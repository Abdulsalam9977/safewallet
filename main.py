from datetime import datetime

import bcrypt
import hashlib
import hmac
import uuid
import smtplib
from email.mime.text import MIMEText
import pyotp
import base64

import requests


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(),salt).decode()
    return hashed

bcrypt.hashpw("".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_hashed_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def unique_id():
    return str(uuid.uuid4())

otp_requirement = 50000

your_secret = 'Abdulsalam'


def generate_otp(email):
    # your_secret ='Abdulsalam'
    h = hmac.new("your secret key".encode('utf-8'), email.encode('utf-8'), hashlib.sha256)
    digest = h.digest()

    user_secret = base64.b32encode(digest).decode('utf-8')
    totp = pyotp.TOTP(user_secret, digits=6,interval=120)

    otp = totp.now()

    return otp

def verify_otp(email,otp):
    h = hmac.new("your secret key".encode('utf-8'), email.encode('utf-8'), hashlib.sha256)
    digest = h.digest()

    user_secret = base64.b32encode(digest).decode('utf-8')
    totp = pyotp.TOTP(user_secret, digits=6,interval=120)
    return totp.verify(otp)


def send_email(email,otp):
    body = f'this is your otp to verify your account: {otp}'
    message = MIMEText(body)
    message['Subject'] = 'Your OTP'
    message['From'] = 'ishaqabdulsalam811@gmail.com'
    message['To'] = email


    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('ishaqabdulsalam811@gmail.com', 'ryid rqnl rhrh nhax')
        server.sendmail(message['From'],message['To'], message.as_string())

# send_email()


def send_alert(email, subject, body):
    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = 'ishaqabdulsalam811@gmail.com'
    message['To'] = email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('ishaqabdulsalam811@gmail.com', 'ryid rqnl rhrh nhax')
        server.sendmail(message['From'], message['To'], message.as_string())


def generate_ip(ip_address):
    url = "http://ipapi.co/{ip_address}/json"

    addr = requests.get(url).json()

    city = addr['city']
    region = addr['region']
    country = addr['country']

    address = f"near {city}, {region}, {country}"

    return address

def send_mail(email,body,subject):
    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = 'ishaqabdulsalam811@gmail.com'
    message['To'] = email


    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('ishaqabdulsalam811@gmail.com', 'ryid rqnl rhrh nhax')
        server.sendmail(message['From'],message['To'], message.as_string())

    return True


# def send_login_alert(email,ip_address):
#     timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
#     address = generate_ip(ip_address)
#     body = f"a new login was detected on your account {address} at {timestamp}"
#     subject = "Login Alert"
#
#     if send_mail(email,body,subject):
#         return True
#
#     return False
