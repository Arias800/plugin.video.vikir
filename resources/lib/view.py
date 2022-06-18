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

try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus

import xbmcvfs
import xbmcgui
import xbmcplugin

# keys allowed in setInfo
types = ["count", "size", "date", "genre", "country", "year", "episode", "season", "sortepisode", "top250", "setid",
         "tracknumber", "rating", "userrating", "watched", "playcount", "overlay", "cast", "castandrole", "director",
         "mpaa", "plot", "plotoutline", "title", "originaltitle", "sorttitle", "duration", "studio", "tagline", "writer",
         "tvshowtitle", "premiered", "status", "set", "setoverview", "tag", "imdbnumber", "code", "aired", "credits",
         "lastplayed", "album", "artist", "votes", "path", "trailer", "dateadded", "mediatype", "dbid"]


def endofdirectory(args):
    # let xbmc know the script is done adding items to the list
    xbmcplugin.endOfDirectory(handle=int(args._argv[1]))


def add_item(args, info, isFolder=True, total_items=0, mediatype="video"):
    """Add item to directory listing.
    """
    # create list item
    li = xbmcgui.ListItem(label=info["title"])

    # get infoLabels
    infoLabels = make_infolabel(args, info)

    # get url
    u = build_url(args, info)
    types = infoLabels.get('mediatype', 'addons')

    li.setInfo("video", infoLabels)
    if not isFolder:
        li.setProperty("IsPlayable", "true")

    # set media image
    li.setArt({"thumb": info.get("thumb", "DefaultFolder.png"),
               "poster": info.get("thumb", "DefaultFolder.png"),
               "banner": info.get("thumb", "DefaultFolder.png"),
               "fanart": info.get("fanart", xbmcvfs.translatePath(args._addon.getAddonInfo("fanart"))),
               "icon": info.get("thumb", "DefaultFolder.png")})

    xbmcplugin.setContent(int(args._argv[1]), types)
    if types == "episodes":
        # sort methods are required in library mode
        xbmcplugin.addSortMethod(int(args._argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

    # add item to list
    xbmcplugin.addDirectoryItem(handle=int(args._argv[1]),
                                url=u,
                                listitem=li,
                                isFolder=isFolder,
                                totalItems=total_items)


def quote_value(value, PY2):
    """Quote value depending on python
    """
    if PY2:
        if not isinstance(value, basestring):
            value = str(value)
        return quote_plus(value.encode("utf-8") if isinstance(value, unicode) else value)
    else:
        if not isinstance(value, str):
            value = str(value)
        return quote_plus(value)


def build_url(args, info):
    """Create url
    """
    s = ""
    # step 1 copy new information from info
    for key, value in list(info.items()):
        if value:
            s = s + "&" + key + "=" + quote_value(value, args.PY2)

    # step 2 copy old information from args, but don't append twice
    for key, value in list(args.__dict__.items()):
        if value and key in types and not "&" + str(key) + "=" in s:
            s = s + "&" + key + "=" + quote_value(value, args.PY2)
    return args._argv[0] + "?" + s[1:]


def make_infolabel(args, info):
    """Generate infoLabels from existing dict
    """
    infoLabels = {}
    # step 1 copy new information from info
    for key, value in list(info.items()):
        if value and key in types:
            infoLabels[key] = value

    # step 2 copy old information from args, but don't overwrite
    for key, value in list(args.__dict__.items()):
        if value and key in types and key not in infoLabels:
            infoLabels[key] = value

    return infoLabels
