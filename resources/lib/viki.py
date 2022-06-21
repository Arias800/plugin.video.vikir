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

import inputstreamhelper
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from . import api
from . import view
from . import model
from . import controller
from resources.lib.util import convertLang


def main(argv):
    """Main function for the addon
    """
    args = model.parse(argv)

    # inputstream adaptive settings
    if hasattr(args, "mode") and args.mode == "hls":
        is_helper = inputstreamhelper.Helper("hls")
        if is_helper.check_inputstream():
            xbmcaddon.Addon(id="inputstream.adaptive").openSettings()
        return True

    args._auth_token = args._addon.getSetting("auth_token")
    args._user_id = args._addon.getSetting("user_id")

    # get subtitle language
    args._lang = convertLang(args._addon.getSetting('lang'))

    # login
    if api.start(args):
        # list menue
        xbmcplugin.setContent(int(args._argv[1]), "addons")
        check_mode(args)
        api.close(args)
    else:
        # login failed
        xbmc.log("[PLUGIN] %s: Login failed" % args._addonname, xbmc.LOGERROR)
        view.add_item(args, {"title": args._addon.getLocalizedString(30060)})
        view.endofdirectory(args)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30060))
        return False


def check_mode(args):
    """Run mode-specific functions
    """
    if hasattr(args, "mode"):
        mode = args.mode
    else:
        mode = None

    if not mode:
        showMainMenue(args)
    elif mode == "search":
        controller.search(args)
    elif mode == "index":
        controller.index(args)
    elif mode == "listEpisode":
        controller.episode(args)
    elif mode == "genre":
        controller.genre(args)
    elif mode == "contry":
        controller.country(args)
    elif mode == "videoplay":
        controller.startplayback(args)
    elif mode == "series" or mode == "movies":
        showCategoriesMenue(args, mode)
    else:
        # unkown mode
        xbmc.log("[PLUGIN] %s: Failed in check_mode '%s'" % (args._addonname, str(mode)), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(args._addonname, args._addon.getLocalizedString(30061), xbmcgui.NOTIFICATION_ERROR)
        showMainMenue(args)


def showMainMenue(args):
    """Show main menu
    """
    # Search
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30040),
                   "mode": "search",
                   "series_id": "search.json"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30038),
                   "mode": "movies"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30039),
                   "mode": "series"})
    # Latest clip
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30054),
                   "mode": "index",
                   "series_id": "clips.json?sort=newest_video"})
    view.endofdirectory(args)


def showCategoriesMenue(args, genre):
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30042),
                   "mode": "genre",
                   "series_id": genre})
    # By Country
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30043),
                   "mode": "contry",
                   "series_id": genre})
    # Latest
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30044),
                   "mode": "index",
                   "series_id": genre + ".json?sort=newest_video"})
    # Recent popular
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30045),
                   "mode": "index",
                   "series_id": genre + ".json?sort=viewed"})
    # Trending
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30046),
                   "mode": "index",
                   "series_id": genre + ".json?sort=all_time"})
    # Best
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30047),
                   "mode": "index",
                   "series_id": genre + ".json?sort=average_rating"})
    view.endofdirectory(args)