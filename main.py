import json
import random
import os.path
import sqlite3
import warcraftograph
from flask import Flask, request, render_template, send_file
app = Flask(__name__)

PORT = 8084
DB_FILE = './db_secrets.db'
EXCUSES = [ "Sorry, our murlocs can't find your secret! Are your sure that it was stored?",
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

@app.route('/show/secrets', methods = ['POST'])
def show_secrets():
    secret_name = request.form['name']

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    query = '''
        SELECT count(*) FROM secrets
        WHERE name = ? AND public = 1
        '''
    c.execute(query.replace('?','"%s"'%secret_name))

    if c.fetchone()[0] > 0:
        c = db.cursor()
        query = '''
            SELECT id FROM secrets
            WHERE name LIKE ? AND public = 1
            '''
        c.execute(query, [secret_name])
        secrets = [(secret_name,'/api/image/%d'%row[0]) for row in c]
        cssclass = "img-thumbnail"
    else:
        msg = random.choice(EXCUSES)
        secrets = [(msg, "/api/image/nosuchsecret")]
        cssclass = ""

    return render_template('secret.html', secrets=secrets, cssclass = cssclass)

@app.route('/secret/<int:id>')
def get_secret_by_id(id):
    db = sqlite3.connect(DB_FILE)
    id = str(id)

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

    return render_template('secret.html', secrets=[(secret_name,fname)], cssclass=cssclass)

@app.route('/store')
def store_secret():
    return render_template('store_secret.html', mind_id=random.randint(1,700))

@app.route('/api/image/<id>')
def get_image(id):
    if id == "nosuchsecret":
        return send_file("static/nosecret.png", mimetype="image/png")

    fname = "cache/%s.jpg" % (id)
    # If the secret has been already cached
    if not os.path.isfile(fname):
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
        query = '''
            SELECT secret FROM secrets
            WHERE id = ?
            '''
        c.execute(query, [id])
        secret = c.fetchone()[0]
        warcraftograph.encode(secret, fname)

    return send_file(fname, mimetype="image/jpeg")

@app.route('/api/get', methods = ['GET'])
def api_get_secret():
    #TODO
    return "OK"

@app.route('/api/store', methods = ['POST'])
def api_store_secret():
    print request.form
    secret_name = request.form['name']
    secret = request.form['secret']
    if 'public' in request.form:
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
        SELECT id FROM secrets
        WHERE name = ? AND secret = ?
        '''
    c.execute(query, (secret_name, secret))

    url = '/secret/' + str(c.fetchone()[0])
    message = 'Your secret is successfullly stored in spirit\'s mind and is avaible <b><u><a href="%s">here</a></u></b>'

    result_json = { 'result':'success',
                    'message': message % url
                  }
    return json.dumps(result_json)

if __name__ == "__main__":

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    cmd = '''
        CREATE TABLE IF NOT EXISTS
            secrets(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                secret TEXT,
                public INTEGER
            )'''
    c.execute(cmd)
    db.commit()

    if not os.path.isdir('cache'):
        os.mkdir("cache")

    app.run ( host = '0.0.0.0', port = PORT, debug=True )
