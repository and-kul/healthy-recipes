import sqlite3
import uuid
import names
import pandas as pd

from flask import Flask, request, jsonify, abort
from flask_cors import cross_origin, CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_SORT_KEYS'] = False


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


def check_exists(uuid):
    with sqlite3.connect("log.db") as conn:
        cursor = conn.cursor()
        cursor.execute('select exists(select 1 from usrs where uuid=?) as lal', (uuid,))
        conn.commit()
    return cursor.fetchone()['lal'] == 1


@app.route("/api/nutritional")
def nutritional():
    if request.headers.get('Authorization') is None or check_exists(request.headers.get('Authorization')):
        abort(403)
    else:
        return jsonify(
            proteins=2.3,
            fats=10.3,
            carbohydrates=13.2
        )


@app.route("/api/topE")
def top_5():
    if request.headers.get('Authorization') is None:  # or check_exists(request.headers.get('Authorization')):
        abort(403)
    else:
        with sqlite3.connect("log.db") as conn:
            val = pd.read_sql(
                "select * from data_subset ds join products_v4 p on ds.ean = p.ean where ds.user_id=='old'", conn)
            e_count = val[[col for col in val.columns if col.startswith('E')]].sum(axis=0)
            return jsonify(e_count.sort_values(ascending=False).iloc[:5].to_dict())


@app.route("/api/stats")
def stats():
    if request.headers.get('Authorization') is None:  # or check_exists(request.headers.get('Authorization')):
        abort(403)
    else:
        with sqlite3.connect("log.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""select TransactionDate as 'month' ,sum(proteins) as 'proteins',
                                    sum(fats) as 'fats',
                                    sum(carbohydrates) as 'carbohydrates',
                                    sum(fats_saturated) as 'fats_saturated',
                                    sum(sugar) as 'sugar'
                                from data_subset ds join products_v4 p on ds.ean = p.ean where ds.user_id=='old' group by TransactionDate""")
            rows = cursor.fetchall()
            arr = []
            for row in rows:
                items = dict(zip([key[0] for key in cursor.description], row))
                # e count
                val = pd.read_sql(
                    "select * from data_subset ds join products_v4 p on ds.ean = p.ean where ds.user_id=='old' and ds.TransactionDate =='" +
                    row[0] + "'", conn)
                e_count = val[[col for col in val.columns if col.startswith('E')]].sum(axis=0)
                res_e = e_count.sort_values(ascending=False).iloc[:5].to_dict()

                arr_e = []
                for k, v in res_e.items():
                    cursor = conn.cursor()
                    cursor.execute(
                        "select name, description, e, danger_level, side_effects from es where es.e=='" + k + "'")
                    rows = cursor.fetchone()
                    vals = dict(zip([key[0] for key in cursor.description], rows))
                    vals.update({"count": v})
                    arr_e.append(vals.copy())
                # bju count
                items.update({"top": arr_e})
                # array final
                arr.append(items.copy())
        return jsonify(arr)


# @app.route("/api/products")
# def products():
#     if request.headers.get('Authorization') is None: # or check_exists(request.headers.get('Authorization')):
#         abort(403)
#     else:
#         req_body = request.get_json()
#         with sqlite3.connect("log.db") as conn:
#             cursor = conn.cursor()
#             cursor.execute(
#                 "select p.pictureUrl as 'picture_url',"
#                 " marketingName_finnish as 'name_fin',"
#                 " marketingName_english as 'name_eng' "
#                 "from data_subset inner join products_v4 p "
#                 "on data_subset.ean = p.ean where data_subset.TransactionDate = '8'")
#             d = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor.fetchall()]
#             conn.commit()
#         return jsonify(d)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
