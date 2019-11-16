import sqlite3
import uuid
import names

from flask import Flask, request, jsonify
from flask_cors import cross_origin, CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/api/login', methods=["GET", "POST"])
def login():
    req_body = request.get_json()
    print(req_body)
    user_token = str(uuid.uuid4())
    print(user_token)
    name = names.get_first_name()
    surname = names.get_last_name()
    with sqlite3.connect("log.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
        create table if not exists usrs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid UUID NOT NULL,
                card_id INTEGER NOT NULL,
                user_name TEXT NOT NULL, 
                user_surname TEXT NOT NULL 
                );''')
        cursor.execute(
            'INSERT INTO usrs(uuid,card_id,user_name,user_surname) values(?, ?, ?, ?)',
            (user_token, req_body['card_id'], name, surname))
        conn.commit()
    return jsonify(
        token=user_token,
        card_id=req_body['card_id'],
        name=name,
        surname=surname
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0')
