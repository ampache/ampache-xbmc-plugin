from future import standard_library
from future.utils import PY2
standard_library.install_aliases()
from builtins import str
from builtins import object
import hashlib
import ssl
import socket
import time
import urllib.request, urllib.parse, urllib.error
import xbmc, xbmcaddon, xbmcgui
import sys
import xml.etree.ElementTree as ET

#main plugin library
from resources.lib import json_storage
from resources.lib import utils as ut
from resources.lib.art_clean import clean_settings

class AmpacheConnect(object):
    
    class ConnectionError(Exception):
        pass
    
    class ConnectionPool:
        _instance = None

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super(AmpacheConnect.ConnectionPool, cls).__new__(cls)
                cls._instance._pool = {}
                cls._instance._max_connections = 5
                cls._instance._timeout = 300
            return cls._instance

        def get_connection(self, server_id):
            if not server_id in self._pool:
                self._pool[server_id] = {'connection': None, 'timestamp': 0, 'in_use': False}

            entry = self._pool[server_id]
            current_time = time.time()

            if entry['connection'] is None or entry['in_use']:
                return None

            if current_time - entry['timestamp'] > self._timeout:
                self._pool[server_id] = {'connection': None, 'timestamp': 0, 'in_use': False}
                return None

            entry['in_use'] = True
            entry['timestamp'] = current_time
            return entry['connection']

        def release_connection(self, server_id, connection):
            if server_id in self._pool:
                self._pool[server_id]['connection'] = connection
                self._pool[server_id]['in_use'] = False
                self._pool[server_id]['timestamp'] = time.time()
 
        def clear_stale_connections(self):
            current_time = time.time()
            for server_id in list(self._pool.keys()):
                if current_time - self._pool[server_id]['timestamp'] > self._timeout and not self._pool[server_id]['in_use']:
                    del self._pool[server_id]
    
    def __init__(self):
        self._ampache = xbmcaddon.Addon("plugin.audio.ampache")
        jsStorServer = json_storage.JsonStorage("servers.json")
        serverStorage = jsStorServer.getData()
        self._connectionData = serverStorage["servers"][serverStorage["current_server"]]
        self._connection_pool = AmpacheConnect.ConnectionPool()
        #self._connectionData = None
        self.filter=None
        self.add=None
        self.limit=None
        self.offset=None
        self.type=None
        self.exact=None 
        self.mode=None
        self.id=None
        self.rating=None
        #force the latest version on the server
        self.version="680001"

    def getBaseUrl(self):
        return '/server/xml.server.php'

    def fillConnectionSettings(self,tree,nTime):
        clean_settings()
        token = tree.findtext('auth')
        version = tree.findtext('api')
        if not version:
        #old api
            version = tree.findtext('version')
        #setSettings only string or unicode
        self._ampache.setSetting("api-version",version)
        self._ampache.setSetting("artists", tree.findtext("artists"))
        self._ampache.setSetting("albums", tree.findtext("albums"))
        self._ampache.setSetting("songs", tree.findtext("songs"))
        apiVersion = int(version)
        if apiVersion < 500001:
            self._ampache.setSetting("playlists", tree.findtext("playlists"))
        else:
            self._ampache.setSetting("playlists", tree.findtext("playlists_searches"))
        self._ampache.setSetting("videos", tree.findtext("videos") )
        self._ampache.setSetting("podcasts", tree.findtext("podcasts") )
        self._ampache.setSetting("live_streams", tree.findtext("live_streams") )
        self._ampache.setSetting("session_expire", tree.findtext("session_expire"))
        self._ampache.setSetting("add", tree.findtext("add"))
        self._ampache.setSetting("token", token)
        #not 24000 seconds ( 6 hours ) , but 2400 ( 40 minutes ) expiration time
        self._ampache.setSetting("token-exp", str(nTime+2400))

    def getCodeMessError(self,tree):
        errormess = None
        errornode = tree.find("error")
        if errornode is not None:
            #ampache api 4 and below
            try:
                errormess = tree.findtext('error')
                return errormess
            except:
                #do nothing
                pass
            #ampache api 5 and above
            try:
                errormess = errornode.findtext("errorMessage")
                return errormess
            except:
                #do nothing
                pass

        return errormess

    def getHashedPassword(self,timeStamp):
        enablePass = self._connectionData["enable_password"]
        if enablePass:
            sdf = self._connectionData["password"]
        else:
            sdf = ""
        hasher = hashlib.new('sha256')
        sdf = sdf.encode()
        hasher.update(sdf)
        myKey = hasher.hexdigest()
        hasher = hashlib.new('sha256')
        timeK = timeStamp + myKey
        timeK = timeK.encode()
        hasher.update(timeK)
        passwordHash = hasher.hexdigest()
        return passwordHash

    def get_user_pwd_login_url(self,nTime):
        myTimeStamp = str(nTime)
        myPassphrase = self.getHashedPassword(myTimeStamp)
        myURL = self._connectionData["url"] + self.getBaseUrl() + '?action=handshake&auth='
        myURL += myPassphrase + "&timestamp=" + myTimeStamp
        myURL += '&version=' + self.version + '&user=' + self._connectionData["username"]
        return myURL

    def get_auth_key_login_url(self):
        myURL = self._connectionData["url"] +  self.getBaseUrl() + '?action=handshake&auth='
        myURL += self._connectionData["api_key"]
        myURL += '&version=' + self.version
        return myURL

    def handle_request(self,url):
        xbmc.log("AmpachePlugin::handle_request: url " + url, xbmc.LOGDEBUG)
        ssl_certs_str = self._ampache.getSetting("disable_ssl_certs")
        try:
            req = urllib.request.Request(url)
            if ut.strBool_to_bool(ssl_certs_str):
                if PY2:
                    response = urllib.request.urlopen(req, timeout=400)
                else:
                    gcontext = ssl.create_default_context()
                    gcontext.check_hostname = False
                    gcontext.verify_mode = ssl.CERT_NONE
                    response = urllib.request.urlopen(req, context=gcontext, timeout=400)
                xbmc.log("AmpachePlugin::handle_request: disable ssl certificates",xbmc.LOGDEBUG)
            else:
                if PY2:
                    gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                    response = urllib.request.urlopen(req, context=gcontext, timeout=400)
                else:
                    response = urllib.request.urlopen(req, timeout=400)
                xbmc.log("AmpachePlugin::handle_request: ssl certificates",xbmc.LOGDEBUG)
        except urllib.error.HTTPError as e:
            xbmc.log("AmpachePlugin::handle_request: HTTPError " +\
                    repr(e),xbmc.LOGDEBUG)
            raise self.ConnectionError
        except urllib.error.URLError as e:
            xbmc.log("AmpachePlugin::handle_request: URLError " +\
                    repr(e),xbmc.LOGDEBUG)
            raise self.ConnectionError
        except Exception as e:
            xbmc.log("AmpachePlugin::handle_request: Generic Error "  +\
                    repr(e),xbmc.LOGDEBUG)
            raise self.ConnectionError
        headers = response.headers
        contents = response.read()
        response.close()
        return headers,contents

    def AMPACHECONNECT(self,showok=False):
        socket.setdefaulttimeout(3600)
        self._connection_pool.clear_stale_connections()
        nTime = int(time.time())
        use_api_key = self._connectionData["use_api_key"]
        server_id = self._connectionData["url"]
 
        existing_connection = self._connection_pool.get_connection(server_id)
        if existing_connection:
            xbmc.log("AmpachePlugin::AMPACHECONNECT: Reusing existing connection",xbmc.LOGDEBUG)
        else:
            if ut.strBool_to_bool(use_api_key):
                xbmc.log("AmpachePlugin::AMPACHECONNECT api_key",xbmc.LOGDEBUG)
                myURL = self.get_auth_key_login_url()
            else:
                xbmc.log("AmpachePlugin::AMPACHECONNECT login password",xbmc.LOGDEBUG)
                myURL = self.get_user_pwd_login_url(nTime)
            try:
                headers,contents = self.handle_request(myURL)
            except self.ConnectionError:
                xbmc.log("AmpachePlugin::AMPACHECONNECT ConnectionError",xbmc.LOGDEBUG)
                #connection error
                xbmcgui.Dialog().notification(ut.tString(30198),ut.tString(30202))
                raise self.ConnectionError
            except Exception as e:
                xbmc.log("AmpachePlugin::AMPACHECONNECT: Generic Error " +\
                        repr(e),xbmc.LOGDEBUG)
                raise self.ConnectionError  # Re-raise to propagate the error
            try:
                xbmc.log("AmpachePlugin::AMPACHECONNECT: contents " +\
                        contents.decode(),xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log("AmpachePlugin::AMPACHECONNECT: unable to print contents " + 
                       repr(e) , xbmc.LOGDEBUG)
            try:
                tree=ET.XML(contents)
            except Exception as e:
                xbmc.log("AmpachePlugin::AMPACHECONNECT: XML Parse Error " + repr(e), xbmc.LOGDEBUG)
                raise self.ConnectionError
            errormess = self.getCodeMessError(tree)
            if errormess:
                #connection error
                xbmcgui.Dialog().notification(ut.tString(30198),ut.tString(30202))
                raise self.ConnectionError
            xbmc.log("AmpachePlugin::AMPACHECONNECT ConnectionOk",xbmc.LOGDEBUG)
            if showok:
                    #use it only if notification of connection is necessary, like
                    #switch server, display connection ok and the name of the
                    #current server
                    amp_notif = ut.tString(30203) + "\n" + ut.tString(30181) +\
                        " : " + self._connectionData["name"]
                    #connection ok
                    xbmcgui.Dialog().notification(ut.tString(30197),amp_notif)
            self.fillConnectionSettings(tree,nTime)
            self._connection_pool.release_connection(server_id, time.time())
        return

    #handle request to the xml api that return binary files
    def ampache_binary_request(self,action):
        thisURL = self.build_ampache_url(action)
        try:
            headers,contents  = self.handle_request(thisURL)
        except self.ConnectionError:
            raise self.ConnectionError
        return headers,contents
   
    #handle request to the xml api that return xml content
    def ampache_http_request(self,action):
        thisURL = self.build_ampache_url(action)
        try:
            headers,contents  = self.handle_request(thisURL)
        except self.ConnectionError:
            raise self.ConnectionError
        if PY2:
            contents = contents.replace("\0", "")
        try:
            xbmc.log("AmpachePlugin::ampache_http_request: contents " + \
                    contents.decode(),xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log("AmpachePlugin::ampache_http_request: unable print contents " + \
                    repr(e) , xbmc.LOGDEBUG)
        tree=ET.XML(contents)
        errormess = self.getCodeMessError(tree)
        if errormess:
            raise self.ConnectionError
        return tree
    
    def build_ampache_url(self,action):
        token = self._ampache.getSetting("token")
        thisURL = self._connectionData["url"] +  self.getBaseUrl() + '?action=' + action
        thisURL += '&auth=' + token
        if self.limit:
            thisURL += '&limit=' +str(self.limit)
        if self.offset:
            thisURL += '&offset=' +str(self.offset)
        if self.filter:
            thisURL += '&filter=' +urllib.parse.quote_plus(str(self.filter))
        if self.add:
            thisURL += '&add=' + self.add
        if self.type:
            thisURL += '&type=' + self.type
        if self.mode:
            thisURL += '&mode=' + self.mode
        if self.exact:
            thisURL += '&exact=' + self.exact
        if self.id:
            thisURL += '&id=' + self.id
        if self.rating:
            thisURL += '&rating=' + self.rating
        return thisURL

