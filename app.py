from flask import Flask, request, jsonify, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os, requests

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey")

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.getenv("DB_USER", "root")
app.config['MYSQL_PASSWORD'] = os.getenv("DB_PASS", "")
app.config['MYSQL_DB'] = os.getenv("DB_NAME", "farm2table")
mysql = MySQL(app)

# ---------- ROUTES ----------
@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)", (name,email,password))
    mysql.connection.commit()
    cur.close()
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password FROM users WHERE email=%s", [email])
    user = cur.fetchone()
    cur.close()
    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        return redirect('/')
    return "Login failed"

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    amount = data.get('amount')

    # M-Pesa Sandbox (Daraja API)
    consumer_key = os.getenv("MPESA_KEY")
    consumer_secret = os.getenv("MPESA_SECRET")
    shortcode = os.getenv("MPESA_SHORTCODE")
    passkey = os.getenv("MPESA_PASSKEY")

    r = requests.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        auth=(consumer_key, consumer_secret)
    )
    token = r.json()['access_token']

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "BusinessShortCode": shortcode,
        "Password": passkey,
        "Timestamp": "20240101120000",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": "254700000000",  # replace with input phone
        "PartyB": shortcode,
        "PhoneNumber": "254700000000",
        "CallBackURL": "https://example.com/callback",
        "AccountReference": "Farm2Table",
        "TransactionDesc": "Produce purchase"
    }
    res = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                        json=payload, headers=headers)

    return jsonify({"message": "M-Pesa request sent", "response": res.json()})

if __name__ == "__main__":
    app.run(debug=True)
