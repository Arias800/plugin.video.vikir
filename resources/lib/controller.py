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
import sys
import inputstreamhelper
import json
import base64
import urllib.parse
import hmac
import hashlib
import requests
try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus

import xbmc
import xbmcgui
import xbmcplugin

from . import api
from . import view

_DEVICE_ID = '86085977d'  # used for android api
_APP = '100005a'
_APP_VERSION = '6.11.3'
_APP_SECRET = 'd96704b180208dbb2efa30fe44c48bd8690441af9f567ba8fd710a72badc85198f7472'
Base_API = 'https://api.viki.io'
Manifest_API = "https://manifest-viki.viki.io%s"

UA = 'Mozilla/5.0 (Macintosh; MacOS X10_14_3; rv;93.0) Gecko/20100101 Firefox/93.0'  # За симулиране на заявка от  компютърен браузър


def search(args):
    keyb = xbmc.Keyboard('', 'Search in VIKI® Database')
    keyb.doModal()

    if (keyb.isConfirmed() and len(keyb.getText()) > 0):
        searchText = quote_plus(keyb.getText())
        searchText = searchText.replace(' ', '+')
        searchurl = args.series_id + "?page=1&per_page=50&term=" + searchText
        index(args, searchurl)


def genre(args):
    jsonrsp = api.request(args, "videos/genres.json", None)
    for genre in range(0, len(jsonrsp)):
        url = args.series_id + '.json?sort=newest_video&page=1&per_page=50&genre=' + jsonrsp[genre]['id']
        # add to view
        view.add_item(args,
                      {"title": jsonrsp[genre]['name']['en'],
                       "mediatype": "addons",
                       "mode": "index",
                       "series_id": url},
                      isFolder=True)

    view.endofdirectory(args)
    return True


def country(args):
    jsonrsp = api.request(args, "videos/countries.json", None)
    for country, subdict in jsonrsp.items():
        url = args.series_id + '.json?sort=newest_video&page=1&per_page=50&origin_country=' + country
        lang = subdict['name'].get(args._lang)
        if not lang:
            lang = subdict['name']["en"]

        view.add_item(args,
                      {"title": lang,
                       "mediatype": "addons",
                       "mode": "index",
                       "series_id": url},
                      isFolder=True)

    view.endofdirectory(args)
    return True


def index(args, searchurl=""):
    if searchurl:
        args.series_id = searchurl

    if hasattr(args, "offset"):
        url = args.series_id + "&page=" + args.offset
    else:
        url = args.series_id

    timestamp = str(int(time.time()))
    jsonrsp = api.request(args, url + "&t=" + timestamp + "&per_page=50", None)

    # check for error
    if "response" not in jsonrsp:
        view.add_item(args, {"title": args._addon.getLocalizedString(30061)})
        view.endofdirectory(args)
        return False

    for movie in range(0, len(jsonrsp['response'])):
        currentJSon = jsonrsp['response'][movie]
        try:
            titles = currentJSon['titles'][args._lang]
        except KeyError:
            titles = currentJSon['titles']["en"]

        try:
            poster = str(currentJSon['images']['atv_cover']['url'])
        except KeyError:
            poster = str(currentJSon['images']['poster']['url'])

        try:
            mdes = currentJSon['descriptions'][args._lang]
        except KeyError:
            try:
                mdes = currentJSon['descriptions']["en"]
            except KeyError:
                mdes = ""
        try:
            dur = str(currentJSon['duration'])
        except KeyError:
            dur = ""
        try:
            rating = currentJSon['rating']
        except KeyError:
            rating = ""

        types = "tvshows" if currentJSon['type'] == "series" else "movies"
        if types == "tvshows":
            url = f'{Base_API}/v4/series/{jsonrsp["response"][movie]["id"]}/episodes.json?page=1&per_page=50&app={_APP}&t={timestamp}'
        else:
            try:
                url = str(currentJSon['watch_now']['id'])
            except:
                url = str(currentJSon['id'])

        # add to view
        view.add_item(args,
                      {"title": titles,
                       "plot": mdes,
                       "duration": dur,
                       "rating": rating,
                       "thumb": poster,
                       "fanart": poster,
                       "mediatype": types,
                       "series_id": url if types == "tvshows" else url,
                       "episode_id": url if types == "movies" else "",
                       "mode": "listEpisode" if types == "tvshows" else "videoplay"},
                      isFolder=True if types == "tvshows" else False)

    if len(jsonrsp['response']) == 50:
        view.add_item(args,
                    {"title": args._addon.getLocalizedString(30055),
                    "offset": int(getattr(args, "offset", 1)) + 1,
                    "mode": args.mode,
                    "series_id": args.series_id},
                    isFolder=True)

    view.endofdirectory(args)
    return True


def episode(args):
    # api request
    jsonrsp = api.request(args, args.series_id, None)

    # check for error
    if jsonrsp.get("error"):
        view.add_item(args, {"title": args._addon.getLocalizedString(30061)})
        view.endofdirectory(args)
        return False

    for episode in range(0, len(jsonrsp['response'])):
        try:
            titles = str(jsonrsp['response'][episode]['titles'][args._lang])
        except KeyError:
            try:
                titles = str(jsonrsp['response'][episode]['titles']['en'])
            except KeyError:
                titles = jsonrsp['response'][episode]["container"]['titles']["en"]

        epNum = str(jsonrsp['response'][episode]['number'])
        url = str(jsonrsp['response'][episode]['id'])
        poster = str(jsonrsp['response'][episode]['images']['poster']['url'])
        dur = str(jsonrsp['response'][episode]['duration'])
        rating = str(jsonrsp['response'][episode]['rating'])

        # add to view
        view.add_item(args,
                      {"title": titles,
                       "episode": epNum,
                       "duration": dur,
                       "rating": rating,
                       "thumb": poster,
                       "fanart": poster,
                       "mediatype": "episodes",
                       "series_id": args.series_id,
                       "episode_id": url,
                       "mode": "videoplay"},
                      isFolder=False)

    view.endofdirectory(args)
    return True

def SIGN(args, pth, version=5):
    timestamp = int(time.time())
    rawtxt = f'/v{version}/{pth}?drms=dt1,dt2,dt3&device_id={_DEVICE_ID}&app={_APP}&token={args._auth_token}'
    sig = hmac.new(
        _APP_SECRET.encode('ascii'), f'{rawtxt}&t={timestamp}'.encode('ascii'), hashlib.sha1).hexdigest()
    return Base_API + rawtxt, timestamp, sig


def startplayback(args):
    urlreq, timestamp, sig = SIGN(args, 'playback_streams/' + args.episode_id + '.json', 5)

    req = urllib.request.Request(urlreq)
    req.add_header('User-Agent', UA)
    req.add_header('X-Viki-manufacturer', 'vivo')
    req.add_header('X-Viki-device-model', 'vivo 1606')
    req.add_header('X-Viki-device-os-ver', '6.0.1')
    req.add_header('X-Viki-connection-type', 'WIFI')
    req.add_header('X-Viki-carrier', '')
    req.add_header('X-Viki-as-id', '100005a-1625321982-3932')
    req.add_header('x-viki-app-ver', _APP_VERSION)
    req.add_header('origin', 'https://www.viki.com')
    req.add_header('timestamp', str(timestamp))
    req.add_header('signature', str(sig))
    opener = urllib.request.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    urlreq = f"https://www.viki.com/api/videos/{args.episode_id}?token={args._auth_token}"
    req = urllib.request.Request(urlreq)
    req.add_header('User-Agent', UA)
    req.add_header('x-client-user-agent', UA)
    req.add_header('x-viki-app-ver', _APP_VERSION)
    req.add_header('Referer', 'https://www.viki.com/videos/' + args.episode_id)
    opener = urllib.request.build_opener()
    f = opener.open(req)
    base64elem = json.loads(f.read())['drm']

    decodeData = base64.b64decode(base64elem)
    manifestUrl = json.loads(decodeData)['dt3']

    headers = {
        "User-Agent": UA,
        "Referer": "https://www.viki.com/",
        "Origin": "https://www.viki.com",
    }

    is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
    if is_helper.check_inputstream():
        if jsonrsp:
            li = xbmcgui.ListItem(path="http://127.0.0.1:4920/url=" + jsonrsp['main'][0]['url'])
            li.setMimeType('application/xml+dash')
            li.setContentLookup(False)

            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.adaptive.license_key', manifestUrl + '|%s&Content-Type=|R{SSM}|' % urllib.parse.urlencode(headers))
            li.setProperty('inputstream.adaptive.stream_headers', 'User-Agent=' + urllib.parse.quote_plus(UA) + '&Origin=https://www.viki.com&Referer=https://www.viki.com')
        else:
            xbmc.executebuiltin('Notification(%s,  %s,  %d,  %s)' % ('VIKI®', 'API does not return a result', 4000, "" + 'OverlayLocked.png'))

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=li)