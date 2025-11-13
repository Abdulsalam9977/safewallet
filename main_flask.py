import os

from flask import Flask, request, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename

from db_query import deposit, freeze_wallet, unfreeze_wallet, transfer_funds, register_user, delete_users, \
    login_user, get_user, transfer_funds, withdraw, view_dashboard, get_transactions, connect_db
from main import otp_requirement, generate_otp, verify_otp, send_email, send_alert
from session import r
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/kyc'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.post('/signup')
def register():
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    roles = ['admin', 'user']
    if role:
        if role not in roles:
            return jsonify({
                'error': 'invalid role',
            }),400

    if not all([name, username, email, password]):
        return jsonify({
            "error": 'missing required field(s)',
        }),400
    new = register_user(name, username, email, password, role)
    return jsonify({
        "message": 'user registered successfully',
        "user_id": new,
    }),200
@app.post('/upload-kyc/<user_id>')
def upload_kyc(user_id):
    if 'document' not in request.files or 'identity' not in request.files:
        return jsonify({"error": "both files are required"}), 400

    document_file = request.files['document']
    identity_file = request.files['identity']

    if document_file.filename == '' or identity_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if document_file and allowed_file(document_file.filename) and identity_file and allowed_file(identity_file.filename):
        secure_doc_filename = secure_filename(document_file.filename)
        secure_id_filename = secure_filename(identity_file.filename)
        doc_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_doc_filename)
        id_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_id_filename)

        document_file.save(doc_path)
        identity_file.save(id_path)

        doc_url = url_for('uploaded_file', filename=f"kyc/{secure_doc_filename}", _external=True)
        id_url = url_for('uploaded_file', filename=f"kyc/{secure_id_filename}", _external=True)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE kyc_verification SET document = %s, identity = %s WHERE user_id = %s
        """, (doc_url,id_url,user_id))
        conn.commit()
        conn.close()


        return jsonify({"message": "kyc documents uploaded successfully",
                        "status": 'pending',
                        "document_url": doc_url,
                        "identity_url": id_url
                        }),201
    return jsonify({"error": "file type not allowed"}), 400

@app.get('/uploads/kyc/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.post('/verify-kyc/<username>/<user_id>')
def verify_kyc(username,user_id):
    session_id = request.headers.get('Session-Id')
    if not session_id:
        return jsonify({
            'error': 'session id is required',
        }),400
    viewers_id,viewer_role = session_id.split(':')
    if viewer_role == 'admin':




        data = request.get_json()
        decision = data.get('decision')
        conn = connect_db()
        cursor = conn.cursor()
        if decision == 'approved':

            cursor.execute("""
            UPDATE kyc_verification SET status = 'approved' WHERE user_id = %s
            """, (user_id,))
            conn.commit()
            cursor.execute("""
            UPDATE u_users SET approved = TRUE WHERE user_id = %s
            """, (user_id,))
            conn.commit()
        elif decision == 'declined':
            cursor.execute("""
            UPDATE kyc_verification SET status = 'declined' WHERE user_id = %s
            """, (user_id,))
            conn.commit()
        return jsonify({
            'message': "success",
        }),200
    stored_id = r.get(username)
    unique, role = session_id.split(':')
    if role != 'admin':
        return jsonify({'error': 'unauthorized: only admin can verify users'}), 401
    if stored_id != session_id:
        return jsonify({
            'error': 'invalid or expired session id',
        }), 400


@app.post('/login')
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    response, status = login_user(username, password)
    return jsonify(response), status

@app.post('/deposit')
def deposit_funds():
    data = request.get_json()
    amount = data.get('amount')
    user_id = data.get('user_id')

    if not int(amount) or int(amount) <= 0:
        return jsonify({
            "error": "invalid amount",
        }),400
    response, status = deposit(amount,user_id)
    return jsonify(response), status


@app.post('/transfer')
def transfer():
    session_id = request.headers.get('Session-Id')
    data = request.get_json()
    amount = data.get('amount')
    receiver_username = data.get('receiver_username')
    sender_username = data.get('sender_username')

    if not sender_username:
        return jsonify({"error": "Invalid or expired session"}), 401

    if not session_id:
        return jsonify({
            "error": "session_id is required",
        }),400
    stored_id = r.get(sender_username)
    if stored_id != session_id:
        return jsonify({
            "error": "invalid or expired session id",
        }),400
    user = get_user(sender_username)
    receiver_user = get_user(receiver_username)
    if user['is_frozen']:
        return jsonify({
            "error": "You cannot make this transfer because your account has been frozen",
        }), 400
    if not amount or not receiver_username:
        return jsonify({
            "error": "amount and receiver username are required",
        }),400
    if int(amount) >= otp_requirement:
        otp = generate_otp(user.get('email'))
        send_email(user.get('email'),otp)
        return jsonify({
            "message": "otp has been sent to your email, verify to make this transfer",
        }),200
    message, status = withdraw(amount, user.get('user_id'))
    if status != 200:
        return jsonify(message)
    deposit(amount, receiver_user.get('user_id'))
    user = get_user(sender_username)
    receiver_user = get_user(receiver_username)
    send_alert(user.get('email'), subject= "Money Sent", body= f"Hello {sender_username}, \n\n"
                                                                            f"You sent ${amount} to {receiver_username}.\n"
                                                                            f"Your new balance: ${user.get('balance'):.2f}\n")


    send_alert(receiver_user.get('email'), subject= "Money Received", body= f"Hello {receiver_username}, \n\n"
                                                                            f"You have received ${amount} from {user.get('username')}.\n"
                                                                            f"Your new balance: ${receiver_user.get('balance'):.2f}\n")
    return jsonify({
        "message": "transfer successful",
    }),200

@app.post('/transfer/verify-otp')
def verify():
    session_id = request.headers.get('Session-Id')
    data = request.get_json()
    amount = data.get('amount')
    otp = data.get('otp')
    receiver_username = data.get('receiver_username')
    sender_username = data.get('sender_username')

    if not session_id:
        return jsonify({
            "error": "session_id is required",
        }),400
    stored_id = r.get(session_id)
    if stored_id != session_id:
        return jsonify({
            "error": "invalid or expired session id",
        }),400
    user = get_user(sender_username)
    receiver_user = get_user(receiver_username)

    if verify_otp(user.get('email'), otp):
        message, status = withdraw(amount, user.get('username'))
        if status != 200:
            return jsonify(message)
        deposit(amount, receiver_user.get('user_id'))
        return jsonify({"message":"transfer successful"}), 201
    return jsonify({"message":"transfer failed"}), 401
@app.post('/withdraw/<user_id>')
def withdrawal(user_id):
    session_id = request.headers.get('Session-Id')
    data = request.get_json()
    amount = data.get('amount')
    username = data.get('username')
    if not username:
        return jsonify({
            "error": "username is required",
        }),400
    if not session_id:
        return jsonify({
            "error": "session_id is required",
        }),400
    user = get_user(username)
    stored_id = r.get(username)
    if stored_id != session_id:
        return jsonify({
            "error": "invalid or expired session id",
        }),400
    if user['is_frozen']:
        return jsonify({
            "error": "You cannot withdraw because your account has been frozen",
        }),400
    if not int(amount) or int(amount) <= 0:
        return jsonify({
            "error": "invalid amount",
        }),400
    response, status = withdraw(amount, user_id)
    return jsonify(response), status
@app.get('/view-transactions/<username>')
def view_transactions(username):
    session_id = request.headers.get('Session-Id')
    user = get_user(username)
    if not user:
        return jsonify({
            "error": "user not found",
        }),404
    if not session_id:
        return jsonify({
            "error": "session_id is required",
        }),400
    stored_id = r.get(username)
    if stored_id != session_id:
        return jsonify({
            "error": "invalid or expired session id",
        }),400
    view = get_transactions(user.get("user_id"))
    return jsonify({'message': "here is your transaction history", "transaction_history": view}), 200
@app.get('/<username>/balance')
def get_balance(username):
    session_id = request.headers.get('Session_Id')
    if not session_id:
        return jsonify({
            "error": 'session id is required',
        }),400
    user = get_user(username)
    if user != get_user(username):
        return jsonify({
            "error": 'invalid username',
        }),400
    stored_id = r.get(username)
    if stored_id != session_id:
        return jsonify({
            "error": "invalid or expired session id",
        }),403
    return jsonify({
        "message": f'user balance is ${user["balance"]:.2f}'
    }),200
@app.put('/<username>/freeze')
def freeze_user(username):
    session_id = request.headers.get('Session-Id')
    if not session_id:
        return jsonify({
            "error": 'session id is required',
        }),400
    stored_id = r.get(username)
    unique_id, role = session_id.split(':')
    if role != 'admin':
        return jsonify({
            "error": 'unauthorized',
        }),409
    if stored_id != session_id:
        return jsonify({
            "error": 'invalid or expired session id',
        }),403
    user = freeze_wallet(username)
    if not user:
        return jsonify({
            "error": 'user not found',
        }),404
    return jsonify({
        "message": 'user account frozen successfully',
    }),200

@app.put('/<username>/unfreeze')
def unfreeze_user(username):
    session_id = request.headers.get('Session-Id')
    if not session_id:
        return jsonify({
            "error": 'session id is required',
        }),400
    stored_id = r.get(username)
    unique_id, role = session_id.split(':')
    if role != 'admin':
        return jsonify({
            "error": 'unauthorized',
        }),409
    if stored_id != session_id:
        return jsonify({
            "error": 'invalid or expired session id',
        }), 403
    user = unfreeze_wallet(username)
    if not user:
        return jsonify({
            "error": 'user not found',
        }), 404
    return jsonify({
        "message": 'user account has been activated successfully',
    }), 200
@app.get('/<username>/dashboard')
def dashboard_viewer(username):
    session_id = request.headers.get('Session_Id')
    if not session_id:
        return jsonify({
            "error": 'session id is required',
        }),400
    stored_id = r.get(username)
    if stored_id != session_id:
        return jsonify({
            "error": 'invalid or expired session id',
        }),400
    response, status = view_dashboard(username)
    return jsonify(response), status


@app.delete('/remove')
def delete_user():
    data = request.get_json()
    username = data.get("username")
    delete = delete_users(username)
    user = get_user(username)
    if not user:
        return {
            "error": "Invalid username"
        }, 400

    if not delete:
        return jsonify({
            "error": "unable to delete user cos user was not found"
        }),400
    return jsonify({
        "message": "user deleted"
    }),200

if __name__ == '__main__':
    app.run(debug=True)


