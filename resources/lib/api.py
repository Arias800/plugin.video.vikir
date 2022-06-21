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
import requests


class API:
    _DEVICE_ID = '86085977d'
    _APP = '100005a'
    _APP_VERSION = '6.11.3'
    _API_URL_TEMPLATE = 'https://api.viki.io%s'
    _APP_SECRET = 'd96704b180208dbb2efa30fe44c48bd8690441af9f567ba8fd710a72badc85198f7472'
    session = None


def _api_query(args, path, version=4, **kwargs):
    path += '?' if '?' not in path else '&'
    if "playback_streams/" in path:
        query = f'/v{version}/{path}drms=dt1,dt2,dt3&device_id={API._DEVICE_ID}&app={API._APP}&token={args._auth_token}'
    else:
        query = f'/v{version}/{path}app={API._APP}'
    return query + ''.join(f'&{name}={val}' for name, val in kwargs.items())


def _sign_query(args, path, version=4):
    timestamp = int(time.time())
    query = _api_query(args, path, version)
    sig = hmac.new(
        API._APP_SECRET.encode('ascii'), f'{query}&t={timestamp}'.encode('ascii'), hashlib.sha1).hexdigest()
    return timestamp, sig, API._API_URL_TEMPLATE % query


def start(args):
    """Login and session handler
    """

    # lets urllib handle cookies
    API.session = requests.Session()
    API.session.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36",
                           "x-viki-app-ver": API._APP_VERSION,
                           "x-client-user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36",
                           "Content-Type": "application/json; charset=utf-8",
                           "X-Viki-manufacturer": "vivo",
                           "X-Viki-device-model": "vivo 1606",
                           "X-Viki-device-os-ver": "6.0.1",
                           "X-Viki-connection-type": "WIFI",
                           "X-Viki-carrier": "",
                           "X-Viki-as-id": "100005a-1625321982-3932",
                           "origin": "https://www.viki.com"}

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

        timestamp, sig, url = _sign_query(args, "sessions.json", version=5)

        resp = API.session.post(url, json=payload).json()

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


def destroy(args):
    """Destroys session
    """
    args._addon.setSetting("user_id", "")
    args._addon.setSetting("auth_token", "")
    args._auth_token = ""


def request(args, method, options, query=None, failed=False, version=4, isJSON=True):
    """Viki API Call
    """
    # required in every request
    payload = {}

    if "http" not in method:
        if query is None:
            timestamp, sig, url = _sign_query(args, method, version)
            API.session.headers.update({'timestamp': str(timestamp),
                                        "signature": str(sig)})
        else:
            url = API._API_URL_TEMPLATE % _api_query(args, method, version)
    else:
        url = method

    if options:
        # merge payload with parameters
        payload.update(options)
        response = API.session.get(url, data=json.dumps(payload))
    else:
        response = API.session.get(url)

    # parse response
    if isJSON:
        return response.json()
    else:
        return response