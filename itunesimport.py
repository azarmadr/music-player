# S Azhar Madar 2020
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import plistlib

from gi.repository import Gtk
from senf import uri2fsn

from quodlibet import _
from quodlibet import app
from quodlibet import util
from quodlibet.qltk import Icons
from quodlibet.qltk.msg import WarningMessage, ErrorMessage
from quodlibet.util.path import expanduser, normalize_path
from quodlibet.plugins.events import EventPlugin


class iTunesimporter:

    def __init__(self, library):
        self._lib = library
        self._changed_songs = []

    def read(self, plist):
        for track in plist['Tracks'].values():
            try:
                filename = uri2fsn(track['Location']).replace('\\','',2)
            except ValueError:
                continue
            
            song = self._lib.get(normalize_path(filename))
            if not song:
                continue

            has_changed = False

        try:
            track['Rating Computed']
        except KeyError:
            try:
                iRating = track['Rating'] / 100.0
                if song("~#rating") == 0 or song("~#rating") == None:
                    song["~#rating"] = iRating
                    has_changed = True
                elif iRating != song["~#rating"]:
                    avgr = (iRating + song("~#rating")) / 2.0
                    song["~#rating"] = avgr
                    has_changed = True
            except KeyError:
                pass

            try:
                pc = track['Play Count']
                try:
                    pc = song["~#playcount"] + pc
                    song["~#playcount"] = pc
                    has_changed = True
                except KeyError:
                    song["~#playcount"] = pc
                    has_changed = True
            except KeyError:
                pass

            try:
                sc = track['Skip Count']
                try:
                    sc = song["~#skipcount"] + sc
                    song["~#skipcount"] = sc
                    has_changed = True
                except KeyError:
                    song["~#skipcount"] = sc
                    has_changed = True
            except KeyError:
                pass

        try:
            song["~#lastplayed"]
        except KeyError:
            try:
                song["~#lastplayed"] = track['Play Date']
                has_changed = True
            except KeyError:
                pass

        try:
            add_date = int(track['Date Added'].timestamp())
            if song["~#added"] > add_date:
                song['~#added'] = add_date
                has_changed = True
        except KeyError:
            pass

        if has_changed:
            self._changed_songs.append(song)

    def finish(self):
        """Call at the end, also returns amount of imported songs"""

        count = len(self._changed_songs)
        self._library.changed(self._changed_songs)
        self._changed_songs = []
        return count


def do_import(parent, library):
    plist_path = expanduser("~/Music/iTunes/iTunes Music Library.xml")
    importer = iTunesimporter(library)
    try:
        plist = plistlib.readPlist(plist_path)
        importer.read(plist)
    except Exception:
        util.print_exc()
        importer.finish()
        msg = _("Import Failed")
        # FIXME: don't depend on the plugin class here..
        ErrorMessage(parent, iTunesImport.PLUGIN_NAME, msg).run()
    else:
        count = importer.finish()
        msg = _("Successfully imported ratings and statistics "
                "for %d songs") % count
        # FIXME: this is just a warning so it works with older QL
        WarningMessage(parent, iTunesimport.PLUGIN_NAME, msg).run()


class iTunesimport(EventPlugin):
    PLUGIN_ID = "itimport"
    PLUGIN_NAME = ("iTunes Import")
    PLUGIN_DESC = _("Imports ratings and song statistics from iTunes Music Player.")
    PLUGIN_ICON = Icons.DOCUMENT_OPEN

    def PluginPreferences(self, *args):
        button = Gtk.Button(label=_("Start Import"))

        def clicked_cb(button):
            do_import(button, app.library)

        button.connect("clicked", clicked_cb)
        return button
