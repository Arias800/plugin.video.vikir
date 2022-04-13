#  -*- coding: utf-8 -*-
# Библиотеки,  които използват python и Kodi в тази приставка
import re
import sys
import time
import json
import base64

import urllib.request
import urllib.parse
import urllib.error

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

import hashlib
import hmac
import inputstreamhelper

from resources.lib.util import convertLang

__addon_id__ = 'plugin.video.vikir'
__Addon = xbmcaddon.Addon(__addon_id__)
__settings__ = xbmcaddon.Addon(id=__addon_id__)

#  Настройка качеството на видеото
quality = __settings__.getSetting('quality')


#  Поддръжка на Фен канали
fc = __settings__.getSetting('fc')

# Дебъг режим
debug = __settings__.getSetting('debug')

#  Настройка реда на епизодите
d = __settings__.getSetting('direction')
if d == '0':
    d = 'desc'
elif d == '1':
    d = 'asc'

lang = convertLang(__settings__.getSetting('lang'))

_DEVICE_ID = '86085977d'  # used for android api
_APP = '100005a'
_APP_VERSION = '6.11.3'
_APP_SECRET = 'd96704b180208dbb2efa30fe44c48bd8690441af9f567ba8fd710a72badc85198f7472'
Base_API = 'https://api.viki.io'
Manifest_API = "https://manifest-viki.viki.io%s"

#  Деклариране на константи
md = xbmcvfs.translatePath(__Addon.getAddonInfo('path') + "resources/media/")
UA = 'Mozilla/5.0 (Macintosh; MacOS X10_14_3; rv;93.0) Gecko/20100101 Firefox/93.0'  # За симулиране на заявка от  компютърен браузър


#  Меню с директории в приставката
def CATEGORIES():
    if not xbmc.getCondVisibility('system.platform.android'):
        xbmc.executebuiltin('Notification(%s,  %s,  %d,  %s)' % ('VIKI®', 'This addon only work on Android', 4000, md + 'OverlayLocked.png'))
        return False

    addDir('Search', f'{Base_API}/v4/search.json?page=1&per_page=50&app=' + _APP + '&term=', '', 3, md + 'DefaultAddonsSearch.png', "addons")
    addLink('Play video by ID', 'loadbyid', '0', 'True', '', '', 'G', '5.0', 8, md + 'DefaultStudios.png', "addons")
    addDir('Browse Movies by Genre', 'movies', '', 6, md + 'DefaultFolder.png', "addons")
    addDir('Browse Movies by Country', 'movies', '', 7, md + 'DefaultFolder.png', "addons")
    addDir('New Movies', f'{Base_API}/v4/movies.json?sort=newest_video&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Recent Movies', f'{Base_API}/v4/movies.json?sort=views_recent&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Popular Movies', f'{Base_API}/v4/movies.json?sort=trending&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Best Movies', f'{Base_API}/v4/movies.json?sort=views&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Browse Series by Genre', 'series', '', 6, md + 'DefaultFolder.png', "addons")
    addDir('Browse Series by Country', 'series', '', 7, md + 'DefaultFolder.png', "addons")
    addDir('New Series', f'{Base_API}/v4/series.json?sort=newest_video&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Recent Series', f'{Base_API}/v4/series.json?sort=views_recent&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Popular Series', f'{Base_API}/v4/series.json?sort=trending&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Best Series', f'{Base_API}/v4/series.json?sort=views&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")
    addDir('Latest Clips', f'{Base_API}/v4/clips.json?sort=newest_video&page=1&per_page=50&app=' + _APP + '&t=', '', 1, md + 'DefaultFolder.png', "addons")


def INDEX(url):
    timestamp = str(int(time.time()))
    #  print url
    if 'search.json' in url:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url + timestamp)
    req.add_header('User-Agent', UA)
    opener = urllib.request.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    #  Начало на обхождането
    for movie in range(0, len(jsonrsp['response'])):
        if (jsonrsp['response'][movie]['flags']['licensed'] is True or fc == 'true' or debug == 'true'):  # Ако заглавието е лицензирано или са разрешени Фен каналите/дебъг режима
            types = "tvshows" if jsonrsp['response'][movie]['type'] == "series" else "movies"

            try:
                mt = jsonrsp['response'][movie]['titles'][lang]
            except KeyError:
                mt = jsonrsp['response'][movie]['titles']["en"]

            try:
                pos = str(jsonrsp['response'][movie]['images']['atv_cover']['url'])
            except KeyError:
                pos = str(jsonrsp['response'][movie]['images']['poster']['url'])

            if types == "tvshows":
                mdes = jsonrsp['response'][movie]['descriptions'].get(lang, "")
                if mdes == "":
                    mdes = jsonrsp['response'][movie]['descriptions'].get("en", "")

                url = f'{Base_API}/v4/series/{jsonrsp["response"][movie]["id"]}/episodes.json?page=1&per_page=50&app={_APP}&t={timestamp}'
                addDir(mt, url, mdes, 2, pos, types)
            else:
                at = jsonrsp['response'][movie]['author']
                mid = str(jsonrsp['response'][movie]['id'])
                rating = jsonrsp['response'][movie]['rating']
                try:
                    ar = str(jsonrsp['response'][movie]['container']['review_stats']['average_rating'])
                except KeyError:
                    ar = ""
                dur = str(jsonrsp['response'][movie]['duration'])
                hd = str(jsonrsp['response'][movie]['flags']['hd'])
                addLink(mt, mid + '@' + pos + '@' + mt, dur, hd, mt, at, rating, ar, 4, pos, types)

    # Край на обхождането

    # Ако имаме още страници...
    if jsonrsp['more'] is True:
        getpage = re.compile('(.+?)&page=(.+?)&per_page=(.+?)&t=').findall(url)
        for fronturl, page, backurl in getpage:
            newpage = int(page) + 1
            url = fronturl + '&page=' + str(newpage) + '&per_page=' + backurl + '&t='
            # print 'URL OF THE NEXT PAGE IS' + url
            addDir('Next page >>', url, '', 1, md + 'DefaultFolder.png', "addons")


# Разлистване епизодите на сериала
def PREPARE(url):
    timestamp = str(int(time.time()))

    req = urllib.request.Request(url + '&direction=' + d)  # Задаване реда на епизодите
    req.add_header('User-Agent', UA)
    opener = urllib.request.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    # Начало на обхождането
    for episode in range(0, len(jsonrsp['response'])):
        if (jsonrsp['response'][episode]['blocked'] is False or debug == 'true'):  # Проверка за достъпност - блокирано или не
            try:
                tsn = str(jsonrsp['response'][episode]['container']['titles'][lang])
                et = str(jsonrsp['response'][episode]['titles'][lang])
            except KeyError:
                tsn = str(jsonrsp['response'][episode]['container']['titles']['en'])
                try:
                    et = str(jsonrsp['response'][episode]['titles']['en'])
                except KeyError:
                    et = ""

            en = str(jsonrsp['response'][episode]['number'])
            ide = str(jsonrsp['response'][episode]['id'])
            pos = str(jsonrsp['response'][episode]['images']['poster']['url'])
            dur = str(jsonrsp['response'][episode]['duration'])
            ar = str(jsonrsp['response'][episode]['container']['review_stats']['average_rating'])
            hd = str(jsonrsp['response'][episode]['flags']['hd'])
            at = str(jsonrsp['response'][episode]['author'])
            rating = str(jsonrsp['response'][episode]['rating'])
            addLink(tsn + ' Episode ' + en, ide + '@' + pos + '@' + et, dur, hd, et, at, rating, ar, 4, pos, "episodes")
    if len(jsonrsp['response']) == 0:
        addDir('There are no episodes for now', '', '', '', md + 'DefaultFolderBack.png', "addons")
    # Край на обхождането

    # Ако имаме още страници...
    if jsonrsp['more'] is True:
        getpage = re.compile('(.+?)page=(.+?)&per_page').findall(url)
        for fronturl, page in getpage:
            newpage = int(page) + 1
            url = fronturl + 'page=' + str(newpage) + '&per_page=50&app=' + _APP + '&t=' + timestamp
            # print 'URL OF THE NEXT PAGE IS' + url
            addDir('Next page >>', url, '', 2, md + 'DefaultFolder.png', "addons")


# Разлистване по жанр
def GENRE(url):
    xbmcplugin.setContent(int(sys.argv[1]), 'addons')
    req = urllib.request.Request(f'{Base_API}/v4/videos/genres.json?app=' + _APP + '')
    req.add_header('User-Agent', UA)
    opener = urllib.request.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    # Начало на обхождането
    for genre in range(0, len(jsonrsp)):
        addDir(jsonrsp[genre]['name']['en'], f'{Base_API}/v4/' + url + '.json?sort=newest_video&page=1&per_page=50&app=' + _APP + '&genre=' + jsonrsp[genre]['id'] + '&t=', '', 1, md + 'DefaultFolder.png', 'addons')


# Разлистване по държава
def COUNTRY(url):
    xbmcplugin.setContent(int(sys.argv[1]), 'addons')
    req = urllib.request.Request(f'{Base_API}/v4/videos/countries.json?app=' + _APP + '')
    req.add_header('User-Agent', UA)
    opener = urllib.request.build_opener()
    f = opener.open(req)
    jsonrsp = json.loads(f.read())

    for country, subdict in jsonrsp.items():
        addDir(jsonrsp[country]['name']['en'], f'{Base_API}/v4/' + url + '.json?sort=newest_video&page=1&per_page=50&app=' + _APP + '&origin_country=' + country + '&t=', '', 1, md + 'DefaultFolder.png', 'addons')


# Търсачка
def SEARCH(url):
    xbmcplugin.setContent(int(sys.argv[1]), 'season')
    keyb = xbmc.Keyboard('', 'Search in VIKI® Database')
    keyb.doModal()

    if (keyb.isConfirmed() and len(keyb.getText()) > 0):
        searchText = urllib.parse.quote_plus(keyb.getText())
        searchText = searchText.replace(' ', '+')
        searchurl = url.encode('utf-8') + searchText.encode('utf-8', 'ignore')
        searchurl = searchurl.decode('utf-8')
        INDEX(searchurl)
    else:
        addDir('Go to main menu...', '', '', '', md + 'DefaultFolderBack.png', "addons")


# Зареждане на клип по неговото ID
def LOADBYID():
    keyb = xbmc.Keyboard('', 'Enter video ID ...videos/xxxxxxv only')
    keyb.doModal()
    if (keyb.isConfirmed()):
        vid = urllib.parse.quote_plus(keyb.getText())
        PLAY('VIKI®', vid + '@0@50', md + 'DefaultStudios.png')
    else:
        addDir('Go to main menu...', '', '', '', md + 'DefaultFolderBack.png', "addons")


def SIGN(pth, version=5):
    timestamp = int(time.time())
    rawtxt = f'/v{version}/{pth}?drms=dt1,dt2,dt3&device_id={_DEVICE_ID}&app={_APP}'
    sig = hmac.new(
        _APP_SECRET.encode('ascii'), f'{rawtxt}&t={timestamp}'.encode('ascii'), hashlib.sha1).hexdigest()
    return Base_API + rawtxt, timestamp, sig


# Зареждане на видео и субтитри
def PLAY(name, url, iconimage):
    url, thumbnail, plot = url.split("@")

    urlreq, timestamp, sig = SIGN('playback_streams/' + url + '.json', 5)

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

    req = urllib.request.Request("https://www.viki.com/api/videos/" + url)
    req.add_header('User-Agent', UA)
    req.add_header('x-client-user-agent', UA)
    req.add_header('x-viki-app-ver', _APP_VERSION)
    req.add_header('Referer', 'https://www.viki.com/videos/' + url)
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
            li = xbmcgui.ListItem(path=jsonrsp['main'][0]['url'])
            li.setArt({'thumb': thumbnail, 'poster': thumbnail, 'banner': thumbnail, 'fanart': thumbnail, 'icon': thumbnail})
            li.setInfo(type="Video", infoLabels={'Title': name, 'Plot': plot})

            li.setMimeType('application/xml+dash')
            li.setContentLookup(False)

            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.adaptive.license_key', manifestUrl + '|%s&Content-Type=|R{SSM}|' % urllib.parse.urlencode(headers))
            li.setProperty('inputstream.adaptive.stream_headers', 'User-Agent=' + urllib.parse.quote_plus(UA) + '&Origin=https://www.viki.com&Referer=https://www.viki.com')
        else:
            xbmc.executebuiltin('Notification(%s,  %s,  %d,  %s)' % ('VIKI®', 'API does not return a result', 4000, md + 'OverlayLocked.png'))

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=li)


# Модул за добавяне на отделно заглавие и неговите атрибути към съдържанието на показваната в Kodi директория - НЯМА НУЖДА ДА ПРОМЕНЯТЕ НИЩО ТУК
def addLink(name, url, vd, hd, plot, author, rating, ar, mode, iconimage, types):
    u = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.parse.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage, 'poster': iconimage, 'banner': iconimage, 'fanart': iconimage, 'icon': iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Rating": ar})
    liz.setInfo(type="Video", infoLabels={"Duration": vd, "Plot": plot})
    # liz.setInfo( type="Video",  infoLabels={ "PlotOutline": "Това е plotoutline",  "Tagline": "Това е tagline" } )
    liz.setInfo(type="Video", infoLabels={"Studio": author, "Mpaa": rating})
    if hd == 'True':
        liz.addStreamInfo('video', {'width': 1280, 'height': 720})
        liz.addStreamInfo('video', {'aspect': 1.78, 'codec': 'h264'})
    else:
        liz.addStreamInfo('video', {'width': 720, 'height': 480})
        liz.addStreamInfo('video', {'aspect': 1.5, 'codec': 'h264'})
    liz.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
    liz.setProperty("IsPlayable", "true")

    contextmenu = []
    contextmenu.append(('Information', 'XBMC.Action(Info)'))
    liz.addContextMenuItems(contextmenu)

    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    xbmcplugin.setContent(int(sys.argv[1]), types)
    return ok


# Модул за добавяне на отделна директория и нейните атрибути към съдържанието на показваната в Kodi директория - НЯМА НУЖДА ДА ПРОМЕНЯТЕ НИЩО ТУК
def addDir(name, url, plot, mode, iconimage, types):
    u = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.parse.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage, 'poster': iconimage, 'banner': iconimage, 'fanart': iconimage, 'icon': 'DefaultFolder.png'})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot})

    if len(plot) > 0:
        contextmenu = []
        contextmenu.append(('Information', 'XBMC.Action(Info)'))
        liz.addContextMenuItems(contextmenu)

    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(int(sys.argv[1]), types)
    return ok


# НЯМА НУЖДА ДА ПРОМЕНЯТЕ НИЩО ТУК
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


params = get_params()
url = None
name = None
iconimage = None
mode = None

try:
    url = urllib.parse.unquote_plus(params["url"])
except (TypeError, KeyError):
    pass
try:
    name = urllib.parse.unquote_plus(params["name"])
except (TypeError, KeyError):
    pass
try:
    name = urllib.parse.unquote_plus(params["iconimage"])
except (TypeError, KeyError):
    pass
try:
    mode = int(params["mode"])
except (TypeError, KeyError):
    pass

# Списък на отделните подпрограми/модули в тази приставка - трябва напълно да отговаря на кода отгоре
if mode is None or url is None or len(url) < 1:
    CATEGORIES()
elif mode == 1:
    INDEX(url)
elif mode == 2:
    PREPARE(url)
elif mode == 3:
    SEARCH(url)
elif mode == 4:
    PLAY(name, url, iconimage)
elif mode == 5:
    SIGN(url)
elif mode == 6:
    GENRE(url)
elif mode == 7:
    COUNTRY(url)
elif mode == 8:
    LOADBYID()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
