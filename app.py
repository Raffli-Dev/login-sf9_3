from flask import Flask,redirect,url_for,render_template,request,jsonify
from pymongo import MongoClient
import jwt
import os
from os.path import join, dirname
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hashlib

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URL")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app=Flask(__name__)
SECRET_KEY = 'SPARTA'

@app.route('/',methods=['GET'])
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"id": payload["id"]})
        return render_template("index.html", nickname=user_info["nickname"])
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your login token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was an issue logging you in"))

@app.route('/login',methods=['GET'])
def login():
    msg = request.args.get('msg')
    return render_template('login.html', msg=msg)

@app.route('/register',methods=['GET'])
def register():
    return render_template('register.html')

@app.route('/api/register',methods=['POST'])
def api_register():
    id_receive = request.form.get('id_give')
    pw_receive = request.form.get('pw_give')
    nickname_receive = request.form.get('nick_give')
    if not id_receive or not pw_receive or not nickname_receive:
        return jsonify({
            'msg': 'Maaf, input tidak boleh kosong.'
        })
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    terpakai = db.user.find_one({'id': id_receive})
    if terpakai:
        return jsonify({
            'msg': f'Maaf, User {id_receive} sudah dipakai. Silahkan gunakan ID lainnya.'
        })
    else:
        db.user.insert_one({
            'id': id_receive,
            'nickname': nickname_receive,
            'pw': pw_hash
        })
        
        return jsonify({
            'result': 'success'
        })

@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form.get('id_give')
    pw_receive = request.form.get('pw_give')
    if not id_receive or not pw_receive:
        return jsonify({'msg':'Usernmae dan password tidak boleh kosong'})
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    result = db.user.find_one({
        'id': id_receive,
        'pw': pw_hash
    })

    if result:
        payload = {
            "id": id_receive,
            "exp": datetime.utcnow() + timedelta(seconds=3600)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"result": "success", "token": token})
    else:
        return jsonify({
            'result':'fail',
            'msg':'Username & Password is incorrct!!!'
        })

@app.route("/api/nick", methods=["GET"])
def api_valid():
    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        print(payload)
        userinfo = db.user.find_one({"id": payload["id"]}, {"_id": 0})
        return jsonify({"result": "success", "nickname": userinfo["nickname"]})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': 'Token kamu telah expired'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': 'there was error silahkan login kembali'})
if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)

