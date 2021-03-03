#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""^^^ NOTE THE FUCKING SHA-BANG MAN! """

from __future__ import print_function

import inspect
import os
import random
import sys
from enum import Enum
from sys import argv

import bcrypt
import requests
from bs4 import BeautifulSoup

from warcraftograph import warcraftograph

# Make all random more random.
random = random.SystemRandom()

""" <config> """
# SERVICE INFO
PORT = 8084
EXPLOIT_NAME = argv[0]

# DEBUG -- logs to stderr, TRACE -- log HTTP requests
DEBUG = os.getenv("DEBUG", False)
TRACE = os.getenv("TRACE", False)
""" </config> """


def check(host: str):
    name = _gen_secret_name()
    secret = _gen_secret_data()

    s = FakeSession(host, PORT)

    _log(f"Going to save secret '{name}' as public")
    link = _put_api(s, name, secret, is_public=True)
    if _get_from_image(s, link) != secret:
        die(ExitStatus.CORRUPT, "Incorrect flag for public secret")

    _log(f"Ensure we can use like for public posts")
    like_pattern = name[:-1] + "_"
    secrets = _show_secrets(s, like_pattern)
    if name not in secrets:
        _log(f"Got unexpected secrets: {secrets}")
        die(ExitStatus.MUMBLE, f"Can't list my secret using {like_pattern}")
    if secrets[name] != link:
        die(ExitStatus.CORRUPT, f"Got unexpected secret for '{name}': {secrets[name]}")

    _log(f"Ensure Warchief API was not redacted entirely")
    if _is_warchief_api_open(s):  # Will exit on mumble.
        _log(f"WARCHIEF SECRET WAS NOT CHANGED!")

    die(ExitStatus.OK, "Check ALL OK")


def put(host: str, flag_id: str, flag: str):
    s = FakeSession(host, PORT)

    name = _gen_secret_name()
    if _roll(1, 10) > 2:
        _log("Putting flag using REST API")
        flag_link = _put_api(s, name, flag)
        new_id = f"{flag_link}:{name}"
    else:
        _log("Putting flag using HTML form. WARN: FRAGILE!")
        flag_link = _put_html(s, name, flag)
        new_id = f"{flag_link}:{name}"

    print(new_id, flush=True)  # It's our flag_id now! Tell it to jury!
    die(ExitStatus.OK, f"All OK! Saved flag: {new_id}")


def get(host: str, flag_id: str, flag: str):
    try:
        link, name = flag_id.split(sep=":", maxsplit=2)
        if not link.startswith("/api/image/"):
            raise ValueError
    except:
        die(
            ExitStatus.CHECKER_ERROR,
            f"Unexpected flagID from jury: {flag_id}! Are u using non-RuCTF checksystem?",
        )

    s = FakeSession(host, PORT)

    if _roll():
        _log("Getting flag using image access")
        message = _get_from_image(s, link)
        if flag not in message:
            die(ExitStatus.CORRUPT, f"Can't find a flag in {message}")
        die(ExitStatus.OK, f"All OK! Successfully retrieved a flag from {link}")
    else:
        _log("Getting flag using API")
        message = _get_from_api(s, name)
        if flag not in message:
            die(ExitStatus.CORRUPT, f"Can't find a flag in {message}")
        die(
            ExitStatus.OK,
            f"All OK! Successfully retrieved a flag from API by name {name}",
        )


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
        """Mozilla/5.0 (Windows NT 5.1) Gecko/20100101 Firefox/14.0 Opera/12.0""",
    ]

    def __init__(self, host, port):
        super(FakeSession, self).__init__()
        if port:
            self.host_port = "{}:{}".format(host, port)
        else:
            self.host_port = host

    def prepare_request(self, request):
        r = super(FakeSession, self).prepare_request(request)
        r.headers["User-Agent"] = random.choice(FakeSession.USER_AGENTS)
        r.headers["Connection"] = "close"
        return r

    # fmt: off
    def request(self, method, url,
        params=None, data=None, headers=None,
        cookies=None, files=None, auth=None, timeout=None, allow_redirects=True,
        proxies=None, hooks=None, stream=None, verify=None, cert=None, json=None,
    ):
        if url[0] == "/" and url[1] != "/":
            url = "http://" + self.host_port + url
        else:
            url = url.format(host=self.host_port)
        r = super(FakeSession, self).request(
            method, url, params, data, headers, cookies, files, auth, timeout,
            allow_redirects, proxies, hooks, stream, verify, cert, json,
        )
        if TRACE:
            print("[TRACE] {method} {url} {r.status_code}".format(**locals()))
        return r
    # fmt: on


def _put_api(s: FakeSession, name: str, flag: str, is_public=False) -> str:
    try:
        r = s.post(
            "/api/store",
            timeout=10,
            data=dict(
                name=name,  # TODO: generate funny name
                secret=flag,
                public=is_public,
            ),
        )
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to post flag via API: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected /api/store code {r.status_code}")

    try:
        flag_link = r.json()["direct_link"]
        if flag_link:
            return flag_link
        else:
            raise ValueError
    except (ValueError, KeyError):
        die(ExitStatus.MUMBLE, f"No direct_link in {r.text}")


def _put_html(s: FakeSession, name: str, flag: str) -> str:
    try:
        r = s.get("/store", timeout=10)
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to access /store: {e}")

    if "Do not report the Warchief!" not in r.text:
        die(ExitStatus.MUMBLE, f"No private checkbox on /store page")

    if "/api/store" not in r.text:
        die(ExitStatus.MUMBLE, f"Missing form destination on /store")

    try:
        bs = BeautifulSoup(r.text, features="html.parser")

        _log("Looking for form elements")
        form = bs.find("form")
        elem_area = form.find("textarea")
        elem_name = form.find("input", attrs=dict(type="text"))
        elem_checkbox = form.find("input", attrs=dict(type="checkbox"))

        _log("Extracting parameter names")
        name_arg = elem_name.get("name")
        secret_arg = elem_area.get("name")
        checkbox_arg, checkbox_val = elem_checkbox.get("name"), elem_checkbox.get(
            "value"
        )
    except Exception as e:
        die(ExitStatus.MUMBLE, f"Can't parse /store page: {e}")

    args = {
        name_arg: name,
        secret_arg: flag,
        checkbox_arg: checkbox_val,
    }
    _log(f"Putting secret using {args}")
    try:
        r = s.post("/api/store", timeout=10, data=args)
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to access /store: {e}")

    try:
        flag_link = r.json()["direct_link"]
        if flag_link:
            return flag_link
        else:
            raise ValueError
    except (ValueError, KeyError):
        die(ExitStatus.MUMBLE, f"No direct_link in {r.text}")


def _get_from_image(s: FakeSession, link: str) -> str:
    try:
        r = s.get(link, timeout=20, stream=True)
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get flag via image API: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected f{link} code {r.status_code}")

    try:
        r.raw.decode_content = True
        return warcraftograph.decode(r.raw)
    except Exception as e:
        die(ExitStatus.MUMBLE, f"Unexpected error reading body: {e}")


def _get_from_api(s: FakeSession, name: str) -> str:
    try:
        r = s.get(
            "/api/get",
            timeout=10,
            params=dict(
                name=name,
            ),
        )
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get flag via direct API: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected HTTP code {r.status_code} on /api/get")

    try:
        secret = r.json()["secret"]
    except (ValueError, KeyError):
        die(ExitStatus.MUMBLE, f"Incorrect json in /api/get: {r.text}")

    return secret


def _show_secrets(s: FakeSession, name: str) -> {str: str}:
    try:
        r = s.post(
            "/show/secrets",
            timeout=20,
            data=dict(
                name=name,
            ),
        )
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed to get flag via image API: {e}")

    if r.status_code != 200:
        die(ExitStatus.MUMBLE, f"Unexpected code {r.status_code} at /show/secrets")

    res = {}
    try:
        bs = BeautifulSoup(r.text, features="html.parser")
        secrets_div = bs.find(
            "div",
            attrs={
                "class": "inner cover secrets",
            },
        )
        names = secrets_div.find_all("h1")
        links = secrets_div.find_all("img")

        for h1, img in zip(names, links):
            res[h1.get_text()] = img.get("src")
    except Exception as e:
        die(ExitStatus.MUMBLE, f"Can't parse /show/secrets output: {e}")

    return res


def _is_warchief_api_open(s: FakeSession) -> bool:
    payload = b"%"
    default_secret = b"FORDAHORDE"
    try:
        r = s.get(
            "/api/warchief/check",
            timeout=10,
            params=dict(
                secret=payload,
                hash=bcrypt.hashpw(payload + default_secret, bcrypt.gensalt()),
            ),
        )
    except Exception as e:
        die(ExitStatus.DOWN, f"Failed check Warchief API: {e}")

    answer = r.text
    if "We have dat secret, chief!" in answer:
        return True
    elif "Proof failed!" in answer:
        return False
    else:
        die(ExitStatus.MUMBLE, f"Unexpected Warchief API answer: {r.text}")


def _roll(a=0, b=1):
    return random.randint(a, b)


def _gen_secret_name() -> str:
    # Note that the result should be random enough, cos we sometimes use it as flag_id.
    # fmt: off
    intros = [
        "Secrets about", "Tactics for", "Loot list of", "Plans to assault",
        "Notes from", "Tips for", "Wipes at", "Tries of", "EP/GP score after",
        "Kill List in", "Looking for raid to", "Mrgles Murgles, mmm",
        "Sexy cows of", "My enemies in",
    ]
    places = [
        "Stormwind City", "Ironforge", "Darnassus", "Gnomeregan", "The Exodar",
        "Gilneas City", "The Vindicaar", "Telogrus Rift", "Shadowforge City",
        "Boralus", "Mechagon City", "Khaz Modan", "Northern Kalimdor",
        "Eastern Kingdoms", "Kul Tiras", "Gnomeregan", "Scarlet Monastery",
        "Razorfen Kraul", "Uldaman", "Razorfen Downs", "Zul’Farrak", "Maraudon",
        "Temple of Atal’Hakkar", "Blackrock Depths", "Lower Blackrock Spire",
        "Upper Blackrock Spire", "Dire Maul", "Scholomance", "Stratholme",
    ]
    # fmt: on
    return f"{random.choice(intros)} {random.choice(places)} #{random.randint(1, 100_000_000_000)}"


def _gen_secret_data(name: str = "") -> str:
    # https://randomwordgenerator.com/sentence.php
    secrets = [
        "Her life in the confines of the house became her new normal.",
        "He always wore his sunglasses at night.",
        "All they could see was the blue water surrounding their sailboat.",
        "Separation anxiety is what happens when you can't find your phone.",
        "He found the chocolate covered roaches quite tasty.",
        "Dan took the deep dive down the rabbit hole.",
        "I may struggle with geography, but I'm sure I'm somewhere around here.",
        "The opportunity of a lifetime passed before him as he tried to decide between a cone or a cup.",
        "The spa attendant applied the deep cleaning mask to the gentleman’s back.",
        "Shakespeare was a famous 17th-century diesel mechanic.",
        "Nudist colonies shun fig-leaf couture.",
        "The beauty of the African sunset disguised the danger lurking nearby.",
        "The secret code they created made no sense, even to them.",
        "The urgent care center was flooded with patients after the news of a new deadly virus was made public.",
        "Greetings from the galaxy MACS0647-JD, or what we call home.",
        "The efficiency we have at removing trash has made creating trash more acceptable.",
        "It dawned on her that others could make her happier, but only she could make herself happy.",
        "Eating eggs on Thursday for choir practice was recommended.",
        "Grape jelly was leaking out the hole in the roof.",
        "The truth is that you pay for your lifestyle in hours.",
        "Honestly, I didn't care much for the first season, so I didn't bother with the second.",
        "There's a message for you if you look up.",
        "She wasn't sure whether to be impressed or concerned that he folded underwear in neat little packages.",
        "The teens wondered what was kept in the red shed on the far edge of the school grounds.",
        "At that moment he wasn't listening to music, he was living an experience.",
        "As he waited for the shower to warm, he noticed that he could hear water change temperature.",
        "He found his art never progressed when he literally used his sweat and tears.",
        "He excelled at firing people nicely.",
    ]

    if name:
        name = f"I know you wanted to find here {name}, but it's better! Here is my secret\n:"
    return name + random.choice(secrets)


def _log(obj):
    if DEBUG and obj:
        caller = inspect.stack()[1].function
        print(f"[{caller}] {obj}", file=sys.stderr)
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
        die(
            ExitStatus.CHECKER_ERROR,
            f"Usage: {argv[0]} check|put|get IP FLAGID FLAG",
        )


if __name__ == "__main__":
    _main()
