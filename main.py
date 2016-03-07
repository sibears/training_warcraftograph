import json
import os.path
import sqlite3
#import warcraftograph
from flask import Flask, make_response, render_template
app = Flask(__name__)

PORT = 8084

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/get')
def get_secret():
    return render_template('get_secret.html')

@app.route('/secret/<int:id>')
def get_secret(id):
    fname = "static/cache/%d.jpg" % (id)
    # If the secret hasn't been cached yet
    if not os.path.isfile(fname):
        c = db.cursor()
        query = '''
            SELECT name, secret FROM secrets
            WHERE id = ?
            '''
        c.execute(query, (id))
        secret_name, secret = c.fetchone()
        if not secret:
            id = "nosuchsecret"
            secret_name = "No such secret!"
        else:
            #img = warcraftograph.encode(secret, fname)
    return render_template('secret.html', name=secret_name, id=id)

@app.route('/store')
def store_secret():
    return render_template('store_secret.html')

@app.route('/api/get', methods = ['GET'])
def api_get_secret():
    secret_name = request.form['name']
    c = db.cursor()
    query = '''
        SELECT count(*) FROM secrets
        WHERE name = ? AND public = 1
        '''
    c.execute(query.replace('?',secret_name))
    if c.fetchone()[0] > 0:
        c = db.cursor()
        query = '''
            SELECT secret FROM secrets
            WHERE name = ? AND public = 1
            '''
        c.execute(query, (secret_name))
        secret_json = {'secrets': [row[0] for row in c]}
    else:
        secret_json = {'secrets': []}
    return json.dumps(secret_json)

@app.route('/api/store', methods = ['POST'])
def api_store_secret():
    secret_name = request.form['name']
    secret = request.form['secret']
    is_public = request.form['public']
    if is_public:
        is_public = 1
    else:
        is_public = 0

    c = db.cursor()
    query = '''
        INSERT INTO secrets(name, secret, public)
        VALUES (?,?,?)
        '''
    c.execute(query, (secret_name, secret, is_public))
    db.commit()

    result_json = {"result":"sucess"}
    return json.dumps(result_json)

if __name__ == "__main__":
    global db
    db = sqlite3.connect('./db_secrets.db')

    c = db.cursor()
    cmd = '''
        CREATE TABLE IF NOT EXISTS
            secrets(
                id INTEGER AUTOINCREMENT,
                name TEXT,
                secret TEXT,
                public INTEGER
            )'''
    c.execute(cmd)
    db.commit()

    app.run ( host = '0.0.0.0', port = PORT, debug=True )
