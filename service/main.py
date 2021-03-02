import json
import os.path
import random
import sqlite3
from hashlib import md5

import bcrypt
from flask import Flask, request, render_template, send_file

import warcraftograph

app = Flask(__name__)

PORT = 8084
DB_FILE = './db_secrets.db'
# don't forget to change it, my Lord
WARCHIEF_SECRET = 'FORDAHORDE'
EXCUSES = ["Sorry, our murlocs can't find your secret! Are your sure that it was stored?",
           "Our shaman gets into the astral storm. The only thing he told us before become insane 'Nhhossuch zzecret'",
           "Secrets? No such secrets! But u look like a fresh meeeeeat",
           "Doez your secret sounds like 'Mrglw mrlrlrlgl mrgl'? If no - i can't find it!",
           "Did u give money to lil' Muergll? No money - no secrets, greeny-skinny!"
           ]


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/get')
def get_secret():
    return render_template('get_secret.html')


@app.route('/show/secrets', methods=['POST'])
def show_secrets():
    try:
        secret_name = request.form['name']
    except:
        return "Wrong arguments"

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    query = '''
        SELECT count(*) FROM secrets
        WHERE name = ? AND public = 1
        '''
    c.execute(query.replace('?', '"%s"' % secret_name))

    if c.fetchone()[0] > 0:
        c = db.cursor()
        query = '''
            SELECT id FROM secrets
            WHERE name LIKE ? AND public = 1
            '''
        c.execute(query, [secret_name])
        secrets = [(secret_name, '/api/image/%s' % row[0]) for row in c]
        cssclass = "img-thumbnail"
    else:
        msg = random.choice(EXCUSES)
        secrets = [(msg, "/api/image/nosuchsecret")]
        cssclass = ""

    return render_template('secret.html', secrets=secrets, cssclass=cssclass)


@app.route('/secret/<id>')
def get_secret_by_id(id):
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    query = '''
        SELECT name FROM secrets
        WHERE id = ?
        '''
    c.execute(query, [id])
    result = c.fetchone()

    if not result:
        fname = "/api/image/nosuchsecret"
        secret_name = random.choice(EXCUSES)
        cssclass = ""
    else:
        fname = "/api/image/" + id
        secret_name = result[0]
        secret_name = '"%s"' % secret_name
        cssclass = "img-thumbnail"

    return render_template('secret.html', secrets=[(secret_name, fname)], cssclass=cssclass)


@app.route('/store')
def store_secret():
    return render_template('store_secret.html', mind_id=random.randint(1, 700))


@app.route('/api/image/<path:id>')
def get_image(id):
    if id == "nosuchsecret":
        return send_file("static/nosecret.png", mimetype="image/png")

    # If the secret has been already cached
    fname = "cache/" + id
    if not os.path.isfile(fname):
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
        query = '''
            SELECT secret FROM secrets
            WHERE id = ?
            '''
        c.execute(query, [id])
        result = c.fetchone()
        if result:
            secret = result[0]
            warcraftograph.encode(secret, fname)
        else:
            return send_file("static/nosecret.png", mimetype="image/png")

    return send_file(fname, mimetype="image/jpeg")


@app.route('/api/warchief/check')
def check_secret():
    try:
        secret = request.args.get('secret')
        user_hash = request.args.get('hash')
    except TypeError:
        return "You are not Warchief, pleb!"
    except:
        return "You need to proof that your are our Warchief!"

    to_hash = ''
    for k, v in request.args.items():
        if k == "hash":
            continue
        to_hash += str(v)

    try:
        if bcrypt.hashpw(to_hash + WARCHIEF_SECRET, user_hash) != user_hash:
            return "Proof failed! Access to the Astral denied!"
    except:
        return "Are you trying to fool me, pleb?!"

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    query = '''
        SELECT count(*) FROM secrets
        WHERE public = 0  AND secret LIKE ?
        '''
    c.execute(query, [secret])

    if c.fetchone()[0] > 0:
        return "We have dat secret, chief!"
    else:
        return "Nobody hides anything like that from your power"


@app.route('/api/get', methods=['GET'])
def api_get_secret():
    # TODO: check select results

    try:
        name = request.args.get('name')
    except:
        return json.dumps({
            "result": "error",
            "message": "Wrong arguments"
        })

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    query = '''
        SELECT secret FROM secrets
        WHERE name LIKE ?
        '''
    c.execute(query, [name])
    result = c.fetchone()

    if result:
        secret = result[0]
        result = {
            'result': 'success',
            'name': name,
            'secret': secret,
        }
        return json.dumps(result)
    return json.dumps({
        "result": "error",
        "message": "No such secret"
    })


@app.route('/api/store', methods=['POST'])
def api_store_secret():
    try:
        secret_name = request.form['name']
        secret = request.form['secret']
    except:
        return json.dumps({
            "result": "error",
            "message": "Wrong arguments"
        })

    if 'public' in request.form and request.form['public']:
        is_public = 1
    else:
        is_public = 0

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    query = '''
        SELECT count(*) FROM secrets
        WHERE name = ? AND secret = ?
        '''
    c.execute(query, (secret_name, secret))

    if int(c.fetchone()[0]) == 0:
        query = '''
            INSERT INTO secrets(name, secret, public)
            VALUES (?,?,?)
            '''
        c.execute(query, (secret_name, secret, is_public))
        db.commit()

    query = '''
        SELECT pid FROM secrets
        WHERE name = ? AND secret = ?
        '''
    c.execute(query, (secret_name, secret))
    pid = c.fetchone()[0]

    m = md5()
    m.update(str(pid).encode())
    id = m.hexdigest()

    query = '''
        UPDATE secrets SET id = ? WHERE pid = ?
        '''
    c.execute(query, (id, pid))
    db.commit()

    url = '/secret/%s' % id
    message = 'Your secret is successfully stored in spirit\'s mind and is available <b><u><a href="%s">here</a></u></b>'

    result_json = {'result': 'success',
                   'message': message % url,
                   'direct_link': '/api/image/%s' % id
                   }
    return json.dumps(result_json)


if __name__ == "__main__":
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    cmd = '''
        CREATE TABLE IF NOT EXISTS
            secrets(
                pid INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT ,
                name TEXT,
                secret TEXT,
                public INTEGER
            )'''
    c.execute(cmd)
    db.commit()

    if not os.path.isdir('cache'):
        os.mkdir("cache")

    app.run(host='0.0.0.0', port=PORT, debug=True)
