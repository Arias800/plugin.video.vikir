# -*- coding: utf-8 -*-
# Viki
# Base structure by 2018 MrKrabat
# Adapted for Viki by Arias800
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import time
import hashlib
import hmac
import json
import xbmcvfs
from os import remove
from os.path import join
import requests
try:
    from urllib2 import urlopen, build_opener, HTTPCookieProcessor, install_opener
except ImportError:
    from urllib.request import urlopen, build_opener, HTTPCookieProcessor, install_opener
try:
    from cookielib import LWPCookieJar
except ImportError:
    from http.cookiejar import LWPCookieJar


class API:
    _DEVICE_ID = '86085977d'
    _APP = '100005a'
    _APP_VERSION = '6.11.3'
    _API_URL_TEMPLATE = 'https://api.viki.io%s'
    _APP_SECRET = 'd96704b180208dbb2efa30fe44c48bd8690441af9f567ba8fd710a72badc85198f7472'


def _api_query(path, version=4, **kwargs):
    path += '?' if '?' not in path else '&'
    query = f'/v{version}/{path}app={API._APP}'
    return query + ''.join(f'&{name}={val}' for name, val in kwargs.items())


def _sign_query(path, version=4):
    timestamp = int(time.time())
    query = _api_query(path, version)
    sig = hmac.new(
        API._APP_SECRET.encode('ascii'), f'{query}&t={timestamp}'.encode('ascii'), hashlib.sha1).hexdigest()
    return timestamp, sig, API._API_URL_TEMPLATE % query


def start(args):
    """Login and session handler
    """
    # create cookiejar
    args._cj = LWPCookieJar()

    # lets urllib handle cookies
    opener = build_opener(HTTPCookieProcessor(args._cj))
    opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36"),
                         ('x-viki-app-ver', API._APP_VERSION),
                         ('Content-Type', 'application/json; charset=utf-8')]
    install_opener(opener)

    # load cookies
    try:
        args._cj.load(getCookiePath(args), ignore_discard=True)
    except IOError:
        # cookie file does not exist
        pass

    # get login informations
    username = args._addon.getSetting("viki_username")
    password = args._addon.getSetting("viki_password")

    # session management
    if not (args._user_id and args._auth_token):
        # create new session
        payload = {
            "password": password,
            "source": {
                "device": "vivo 1606",
                "method": "standard",
                "partner": "viki",
                "platform": "android"
            },
            "user": {
                "registration_method": "standard",
                "source_device": "vivo 1606",
                "source_partner": "viki",
                "source_platform": "android"
            },
            "username": username
        }

        timestamp, sig, url = _sign_query("sessions.json", version=5)

        headers = {'accept-language': 'fr',
                   'timestamp': str(timestamp),
                   'signature': sig,
                   'x-viki-app-ver': '6.12.2',
                   'x-viki-manufacturer': 'vivo',
                   'x-viki-device-model': 'vivo 1606',
                   'x-viki-device-os-ver': '9',
                   'x-viki-connection-type': 'WIFI',
                   'x-viki-carrier': '',
                   'x-viki-as-id': '100005a-1625321982-3932',
                   'content-type': 'application/json; charset=utf-8',
                   'user-agent': 'okhttp/3.12.12'}

        resp = requests.post(url, headers=headers, json=payload).json()

        # check for error
        if resp.get("error"):
            return False
        args._auth_token = resp["token"]
        args._user_id = resp["user"]["id"]
    return True


def close(args):
    """Saves cookies and session
    """
    args._addon.setSetting("user_id", args._user_id)
    args._addon.setSetting("auth_token", args._auth_token)
    if args._cj:
        args._cj.save(getCookiePath(args), ignore_discard=True)


def destroy(args):
    """Destroys session
    """
    args._addon.setSetting("user_id", "")
    args._addon.setSetting("auth_token", "")
    args._auth_token = ""
    args._cj = False
    try:
        remove(getCookiePath(args))
    except WindowsError:
        pass


def request(args, method, options, query=None, failed=False):
    """Viki API Call
    """
    # required in every request
    payload = {}

    if "http" not in method:
        if query is None:
            timestamp, sig, url = _sign_query(method)
        else:
            url = API._API_URL_TEMPLATE % _api_query(method)
    else:
        url = method

    if options:
        # merge payload with parameters
        payload.update(options)
        payload = json.dumps(payload).encode("utf-8")
        response = urlopen(url, payload)
    else:
        response = urlopen(url)

    # parse response
    json_data = response.read().decode("utf-8")
    json_data = json.loads(json_data)
    return json_data


def getCookiePath(args):
    """Get cookie file path
    """
    profile_path = xbmcvfs.translatePath(args._addon.getAddonInfo("profile"))
    if args.PY2:
        return join(profile_path.decode("utf-8"), u"cookies.lwp")
    else:
        return join(profile_path, "cookies.lwp")
