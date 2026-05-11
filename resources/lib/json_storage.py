from builtins import object
from future.utils import PY2
import json
import os
import threading
import xbmc
import xbmcaddon
import xbmcvfs
from copy import deepcopy

#main plugin library

class JsonStorage(object):

    _cache = {}
    _lock = threading.Lock()

    def __init__(self,filename):
        ampache = xbmcaddon.Addon("plugin.audio.ampache")
        if PY2:
            base_dir = xbmc.translatePath( ampache.getAddonInfo('profile'))
            base_dir = base_dir.decode('utf-8')
        else:
            base_dir = xbmcvfs.translatePath( ampache.getAddonInfo('profile'))
        self._filename = os.path.join(base_dir, filename)
        self._data = dict()
        self.load()

    def load(self):
        with JsonStorage._lock:
            if self._filename in JsonStorage._cache:
                self._data = deepcopy(JsonStorage._cache[self._filename])
                return
        if not xbmcvfs.exists(self._filename):
            with JsonStorage._lock:
                JsonStorage._cache[self._filename] = {}
            return
        try:
            with open(self._filename, 'r') as fd:
                self._data = json.load(fd)
        except (ValueError, IOError, OSError):
            self._data = {}
        with JsonStorage._lock:
            JsonStorage._cache[self._filename] = deepcopy(self._data)

    @classmethod
    def invalidate_cache(cls):
        with cls._lock:
            cls._cache.clear()

    def save(self,data):
        if data != self._data:
            self._data = deepcopy(data)
            tmp_filename = self._filename + '.tmp'
            with open(tmp_filename, 'w') as fd:
                json.dump(self._data, fd, indent=4, sort_keys=True)
            if PY2:
                os.rename(tmp_filename, self._filename)
            else:
                os.replace(tmp_filename, self._filename)
            with JsonStorage._lock:
                JsonStorage._cache[self._filename] = deepcopy(self._data)

    def getData(self):
        return deepcopy(self._data)
