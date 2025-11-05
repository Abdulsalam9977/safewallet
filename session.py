import uuid

from dotenv import load_dotenv

import redis,os


# from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
USERNAME = os.getenv('REDIS_USERNAME')
PASSWORD = os.getenv('PASSWORD')

print(HOST, PORT, USERNAME, PASSWORD)
r = redis.Redis(
    host=HOST,
    port= int(PORT),
    decode_responses=True,
    username=USERNAME,
    password=PASSWORD,
)


