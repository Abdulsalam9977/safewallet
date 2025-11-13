import psycopg2 as pg
from psycopg2._psycopg import cursor

from main import hash_password, unique_id, otp_requirement, verify_otp, verify_hashed_password
from session import r


def connect_db():
    return pg.connect(
        host="localhost",
        port="5432",
        database="first-database",
        user="postgres",
        password="2008",
    )


def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS u_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    balance DECIMAL (12,2) DEFAULT 0.00,
    role VARCHAR(32) DEFAULT 'user',
    is_frozen BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT now())
    """)
    conn.commit()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID REFERENCES u_users(user_id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES u_users(user_id) ON DELETE CASCADE,
    amount DECIMAL (12,2) NOT NULL,
    transaction_type VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT now())
    """)
    conn.commit()
    cursor.execute("""
    DROP TABLE kyc_verification;""")
    conn.commit()
    print('table created')


# create_table()
def table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kyc_verification (
    user_id UUID PRIMARY KEY REFERENCES u_users(user_id) ON DELETE CASCADE,
    document TEXT,
    identity TEXT,
    status VARCHAR(20) DEFAULT 'pending'
    )
    """)
    conn.commit()
table()
def register_user(name,username, email, password,role = None,is_frozen = False):
    conn = connect_db()
    cursor = conn.cursor()
    user_id = None
    hash_pw = hash_password(password)
    if role:
        cursor.execute("""
        INSERT INTO u_users (name, username, email, password, role, is_frozen)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING user_id;
        """, (name, username, email, hash_pw,role,is_frozen)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    cursor.execute("""
    INSERT INTO u_users (name, username, email, password,is_frozen)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING user_id, is_frozen
    """, (name, username, email, hash_pw,is_frozen)
    )
    user_id = cursor.fetchone()[0]
    conn.commit()
    return user_id

def get_user(username = None,user_id = None):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM u_users WHERE username = %s OR user_id = %s;
    """, (username,user_id,)
    )
    users = cursor.fetchone()
    user_dict = {}
    if users:
        user_id, name, username, email, password, balance, role, is_frozen, created_at,approved = users

        user_dict["user_id"] = user_id
        user_dict["name"] = name
        user_dict["username"] = username
        user_dict["email"] = email
        user_dict["password"] = password
        user_dict["balance"] = balance
        user_dict["role"] = role
        user_dict["is_frozen"] = is_frozen
        user_dict["created_at"] = created_at
        user_dict["approved"] = approved

        return user_dict
    return None


def login_user(username, password):
    user = get_user(username)
    if not user:
        return {
            "error": "Invalid username or password.",
        },404
    same_password = verify_hashed_password(password,user["password"])
    if not same_password:
        return {
            "error": "Invalid password",
        },400
    session_id = f'{user["user_id"]}:{user["role"]}'
    r.setex(username,3600, session_id)
    return {'status': 'success', 'session_id': session_id}, 200


def deposit(amount, user_id):
    user = get_user(user_id=user_id)
    if not user:
        return {
            "error": "Invalid user_id",
        },400
    if int(amount) < 100:
        return {
            "error": "Invalid amount"
        },400
    if user["approved"] == False:
        return {
            "error": "you cannot perform this action because your account has not been approved.",
        },400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE u_users SET balance = balance + %s where user_id = %s
    RETURNING balance;
    """, (amount,user_id,)
    )
    new_balance = cursor.fetchone()[0]
    conn.commit()
    cursor.execute("""
    INSERT INTO user_transactions (sender_id, receiver_id, amount, transaction_type)
    VALUES (%s, %s, %s, 'deposit')
    """,(user_id,user_id,amount,)
    )
    conn.commit()
    return{
        "message": "deposit successful",
    }, 200

def withdraw(amount, user_id):
    user = get_user(user_id=user_id)
    if not user:
        return {
            "error": "Invalid user_id",
        },400
    if int(amount) <= 0:
        return {
            "error": "Invalid amount"
        },400


    if int(amount) > user.get("balance"):
        return {"error": "Insufficient funds"}, 403
    if user["approved"] == False:
        return {
            "error": "you cannot perform this action because your account has not been approved.",
        },400
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE u_users SET balance = balance - %s where user_id = %s
    RETURNING balance;
    """, (amount,user_id,)
    )
    new_balance = cursor.fetchone()[0]
    conn.commit()
    cursor.execute("""
    INSERT INTO user_transactions (sender_id, receiver_id, amount, transaction_type)
    VALUES (%s, %s, %s, 'transfer')
    """,(user_id,user_id,amount,)
    )
    conn.commit()
    return {"message":"success"}, 200

def update_user_balance(user_id, new_balance):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE u_users SET balance = %s WHERE user_id = %s
    """, (new_balance, user_id,)
    )
def transfer_funds(sender_username,receiver_username,amount):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, balance FROM u_users WHERE username = %s
    """, (sender_username,)
    )
    sender = cursor.fetchone()
    if not sender:
        return {
            "error": "sender not found",
        },404
    sender_id,sender_balance = sender

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, balance FROM u_users WHERE username = %s
    """, (receiver_username,)
    )
    receiver = cursor.fetchone()
    if not sender:
        return {
            "error": "receiver not found",
        },404
    receiver_id,receiver_balance = receiver

    if sender_balance < amount:
        return {
            "error": "Insufficient balance",
        },400



    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE u_users SET balance =  balance - %s WHERE username = %s
    RETURNING balance;
    """, (amount,sender_username,)
    )
    conn.commit()

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE u_users SET balance = + %s WHERE username = %s
    RETURNING balance;
    """, (amount, receiver_username,)
    )
    conn.commit()

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_transactions (sender_id, receiver_id, amount, transaction_type)
    VALUES (%s, %s, %s, 'transfer')
    """, (sender_id,receiver_id,amount,)
    )
    conn.commit()
    return True




def freeze_wallet(username):
    user = get_user(username)
    if not user:
        return False
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE u_users SET is_frozen = TRUE WHERE username = %s;
    """, (username,)
    )
    conn.commit()
    return True
# print(freeze_wallet('abdul00'))

def unfreeze_wallet(username):
    user = get_user(username)
    if not user:
        return False
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE u_users SET is_frozen = FALSE WHERE username = %s;
    """, (username,)
    )
    conn.commit()
    return True
# print(unfreeze_wallet('abdul00'))
def delete_users(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """DELETE FROM u_users WHERE username = %s
        """, (username, )
    )
    conn.commit()
    print('deleted successfully')
    return True
def get_transactions(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM user_transactions WHERE sender_id = %s OR receiver_id = %s;
    """, (user_id,user_id,))
    user = cursor.fetchall()
    data = []
    for row in user:
        data.append({
            "transaction_id": row[0],
            "sender_id": row[1],
            "receiver_id": row[2],
            "amount": row[3],
            "transaction_type": row[4],
            "created_at": row[5]
        })
    return data


def view_dashboard(username):
    user = get_user(username)
    if not user:
        return {
            "error": "invalid user id",
        },400

    dashboard = {
        "user_id": user['user_id'],
        "name": user['name'],
        "username": user['username'],
        "email": user['email'],
        "balance": user['balance'],
        "role": user['role'],
        "is_frozen": user['is_frozen'],
        "created_at": user['created_at'],
        "approved": user['approved'],
    }
    return dashboard,200





