#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""^^^ NOTE THE FUCKING SHA-BANG MAN! """

from __future__ import print_function

import os
import random
import string
import sys
from enum import Enum
from sys import argv

import requests

from warcraftograph import warcraftograph

""" <config> """
# SERVICE INFO
PORT = 8084
EXPLOIT_NAME = argv[0]

# DEBUG enables verbose output of all socket messages
DEBUG = os.getenv("DEBUG", False)
""" </config> """


def check(host: str):
    die(code=ExitStatus.OK)


def put(host: str, flag_id: str, flag: str):
    s = FakeSession(host, PORT)

    _log("Putting flag using REST API")
    try:
        r = s.post("/api/store", timeout=10, data=dict(
            name=flag_id,  # TODO: generate funny name
            secret=flag,
            public=False,
        ))
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to post flag via API: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /api/store code {r.status_code}")

    try:
        flag_link = r.json()["direct_link"]
        if not flag_link: raise ValueError
    except (ValueError, KeyError):
        die(ExitStatus.MUMBLE, f"No direct_link in {r.text}")

    print(flag_link, flush=True)  # It's our flag_id now! Tell it to jury!
    die(ExitStatus.OK, f"All OK! Saved flag link: {flag_link}")


def get(host: str, flag_id: str, flag: str):
    if not flag_id.startswith("/api/image/"):
        die(ExitStatus.CHECKER_ERROR,
            f"Unexpected flagID from jury: {flag_id}! Are u using non-RuCTF checksystem?")

    s = FakeSession(host, PORT)

    # TODO: check get raw secret by name also.

    _log("Getting flag using image access")
    try:
        r = s.get(flag_id, timeout=20, stream=True)
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get flag via image API: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected f{flag_id} code {r.status_code}")

    try:
        r.raw.decode_content = True
        message = warcraftograph.decode(r.raw)
    except Exception as e:
        die(ExitStatus.MUMBLE, f"Unexpected error reading body: {e}")

    if flag not in message:
        die(ExitStatus.CORRUPT, f"Can't find a flag in {message}")
    die(ExitStatus.OK, f"All OK! Successfully retrieved a flag from {flag_id}")


class FakeSession(requests.Session):
    """
        FakeSession reference:
            - `s = FakeSession(host, PORT)` -- creation
            - `s` mimics all standard request.Session API except of fe features:
                -- `url` can be started from "/path" and will be expanded to "http://{host}:{PORT}/path"
                -- for non-HTTP scheme use "https://{host}/path" template which will be expanded in the same manner
                -- `s` uses random browser-like User-Agents for every requests
                -- `s` closes connection after every request, so exploit get splitted among multiple TCP sessions
        Short requests reference:
            - `s.post(url, data={"arg": "value"})`          -- send request argument
            - `s.post(url, headers={"X-Boroda": "DA!"})`    -- send additional headers
            - `s.post(url, auth=(login, password)`          -- send basic http auth
            - `s.post(url, timeout=1.1)`                    -- send timeouted request
            - `s.request("CAT", url, data={"eat":"mice"})`  -- send custom-verb request
            (response data)
            - `r.text`/`r.json()`  -- text data // parsed json object
    """

    USER_AGENTS = [
        """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15""",
        """Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36""",
        """Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201""",
        """Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13; ) Gecko/20101203""",
        """Mozilla/5.0 (Windows NT 5.1) Gecko/20100101 Firefox/14.0 Opera/12.0"""
    ]

    def __init__(self, host, port):
        super(FakeSession, self).__init__()
        if port:
            self.host_port = "{}:{}".format(host, port)
        else:
            self.host_port = host

    def prepare_request(self, request):
        r = super(FakeSession, self).prepare_request(request)
        r.headers['User-Agent'] = random.choice(FakeSession.USER_AGENTS)
        r.headers['Connection'] = "close"
        return r

    def request(self, method, url,
                params=None, data=None, headers=None, cookies=None, files=None,
                auth=None, timeout=None, allow_redirects=True, proxies=None,
                hooks=None, stream=None, verify=None, cert=None, json=None):
        if url[0] == "/" and url[1] != "/":
            url = "http://" + self.host_port + url
        else:
            url = url.format(host=self.host_port)
        r = super(FakeSession, self).request(method, url, params, data, headers, cookies, files,
                                             auth, timeout, allow_redirects, proxies, hooks, stream, verify, cert, json)
        if DEBUG:
            print("[DEBUG] {method} {url} {r.status_code}".format(**locals()))
        return r


def _roll(a=0, b=1):
    return random.randint(a, b)


def _rand_string(n=12, alphabet=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(alphabet) for _ in range(n))


def _log(obj):
    if DEBUG and obj:
        print(obj, file=sys.stderr)
    return obj


class ExitStatus(Enum):
    OK = 101
    CORRUPT = 102
    MUMBLE = 103
    DOWN = 104
    CHECKER_ERROR = 110


def die(code: ExitStatus, msg: str):
    if msg:
        print(msg, file=sys.stderr)
    exit(code.value)


def _main():
    try:
        cmd = argv[1]
        hostname = argv[2]
        if cmd == "get":
            fid, flag = argv[3], argv[4]
            get(hostname, fid, flag)
        elif cmd == "put":
            fid, flag = argv[3], argv[4]
            put(hostname, fid, flag)
        elif cmd == "check":
            check(hostname)
        else:
            raise IndexError
    except IndexError:
        die(ExitStatus.CHECKER_ERROR, f"Usage: {argv[0]} check|put|get IP FLAGID FLAG", )


if __name__ == "__main__":
    _main()
