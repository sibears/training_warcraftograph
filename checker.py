#!/usr/bin/python
from sys import exit, argv, stderr, stdout
import sys
from os import popen
from time import time, sleep
from random import seed, random, randint, choice
from pprint import pformat
from PIL import Image
import md5
import re
import sqlite3
import socket
import telnetlib
import string
import random
import requests
import json
import shutil
import warcraftograph

ERR_OK = 0 # All OK
ERR_CONNECTION = 1 # Connection refused / connection attempt timed out
ERR_WRONGFLAG = 5 # A wrong flag / no flag was returned
ERR_FUNCLACK = 9 # The service lacks functionality
ERR_TIMEOUT = 13 # Done automatically by the scorebot under normal circumstances
ERR_UNKNOWN = 17 # Temporary status -- do not use unless you've got a very good reason to do so
ERR_GENERIC = 21 # Be sure to include a descriptive message if using this error
ERR_PROTOCOL = 25 # Protocol violation

# Add error descriptions here.
# Note (to zeri): do not insult people. ;-)
shit = {'conn':          ("Unable to connect to the service", ERR_CONNECTION),
        'conn_sso':      ("Unable to connect to the SSO", ERR_PROTOCOL),
        'auth_sso':      ("Unable to get authkey from SSO", ERR_FUNCLACK),
        'name':          ("Unable to get username", ERR_FUNCLACK),
        'sso_reg_err':   ("Unable to reg new user", ERR_FUNCLACK),
        'missing url':   ("Unable to get link to secret", ERR_FUNCLACK),
        'firmware_down': ("Unable to download firmware from SSO", ERR_FUNCLACK),
        'firm_func':     ("Unable to use firmware", ERR_FUNCLACK),
        'greeting':      ("The server didn't greet correctly", ERR_PROTOCOL),
        'allok':         ("Everything is fine", ERR_OK),
        'flggg':         ("Wrong flag", ERR_WRONGFLAG),
        'func':          ("Admin wonder why he couldn't manage his service",ERR_FUNCLACK),
       }

def die(reason):
    try: msg, exitcode = shit[reason]
    except: msg, exitcode = reason, 1
    stdout.write(msg)
    stdout.flush()
    exit(exitcode)

def store((ip, flagid, flag)):
    db = sqlite3.connect('./db/store.db')
    c = db.cursor()
    cmd = '''
        CREATE TABLE IF NOT EXISTS
            urls(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flagid TEXT,
                url TEXT
                )'''
    c.execute(cmd)
    db.commit()

    ses = requests.Session()
    try:
        payload = {'name': flagid, 'secret': flag}
        ans = ses.post('http://'+str(ip)+':8084/api/store',data=payload)
    except:
        die('conn')

    try:
        ans_pars = json.loads(ans.text)
        url = ans_pars[u'direct_link']
    except:
        die('missing url')

    c = db.cursor()
    query = '''
        INSERT INTO urls(flagid, url)
        VALUES (?,?)
        '''
    c.execute(query, (flagid, url))
    db.commit()

    sys.stderr.write("===== SUCCESSFULLY STORED FLAG =====\n")
    die('allok')

def retrieve((ip, flagid, flag)):
    db = sqlite3.connect('./db/store.db')
    c = db.cursor()
    c.execute("SELECT url FROM urls WHERE flagid='%s'" % flagid )
    num = c.fetchone()[0]
    print num
    try:
        r = requests.get('http://'+str(ip)+':8084'+num, stream=True)
        if r.status_code == 200:
            with open('./img/'+flagid, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
    except:
        die('conn')

    user_flag = warcraftograph.decode('./img/'+flagid)
    if not user_flag == flag:
        die("flggg")

    print "===== SUCCESSFULLY RETRIEVED FLAG ====="
    die('allok')

def test((ip,)):
    exit(0) # service is fully functional

if __name__ == '__main__':
    {   'store': store,
        'retrieve': retrieve,
        'test': test
    }[argv[1]](tuple(argv[2:]))
try: pass
except SystemExit, e: exit(e.code)
except Exception, e:
    stderr.write("ERROR! ")
    stderr.write(str(e))
    print "Error: " + str(e)
    print "Usage: %s store|retrieve IP FLAGID FLAG" % argv[0]
    print "       %s test IP" % argv[0]
finally: stderr.flush()
