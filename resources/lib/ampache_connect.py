from future import standard_library
from future.utils import PY2
standard_library.install_aliases()
from builtins import str
from builtins import object
import hashlib
import ssl
import socket
import time, urllib.request, urllib.parse, urllib.error,urllib.request,urllib.error,urllib.parse
import xbmc, xbmcaddon
import sys
import xml.etree.ElementTree as ET

from resources.lib import json_storage
from resources.lib import utils

class AmpacheConnect(object):
    
    class ConnectionError(Exception):
        pass
    
    def __init__(self):
        self._ampache = xbmcaddon.Addon()
        jsStorServer = json_storage.JsonStorage("servers.json")
        serverStorage = jsStorServer.getData()
        self._connectionData = serverStorage["servers"][serverStorage["current_server"]]
        #self._connectionData = None
        self.filter=None
        self.add=None
        self.limit=5000
        self.offset=0
        self.type=None
        self.exact=None 
        self.mode=None
        self.id=None
        self.rating=None
  
    def get_user_pwd_login_url(self,nTime):
        myTimeStamp = str(nTime)
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
        timeK = myTimeStamp + myKey
        timeK = timeK.encode()
        hasher.update(timeK)
        myPassphrase = hasher.hexdigest()
        myURL = self._connectionData["url"] + '/server/xml.server.php?action=handshake&auth='
        myURL += myPassphrase + "&timestamp=" + myTimeStamp
        myURL += '&version=' + self._ampache.getSetting("api-version") + '&user=' + self._connectionData["username"]
        return myURL

    def get_auth_key_login_url(self):
        myURL = self._connectionData["url"] + '/server/xml.server.php?action=handshake&auth='
        myURL += self._connectionData["api_key"]
        myURL += '&version=' + self._ampache.getSetting("api-version")
        return myURL

    def handle_request(self,url):
        xbmc.log("AmpachePlugin::handle_request: url " + url, xbmc.LOGDEBUG)
        ssl_certs_str = self._ampache.getSetting("disable_ssl_certs")
        try:
            req = urllib.request.Request(url)
            if utils.strBool_to_bool(ssl_certs_str):
                gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                response = urllib.request.urlopen(req, context=gcontext, timeout=400)
                xbmc.log("AmpachePlugin::handle_request: ssl",xbmc.LOGDEBUG)
            else:
                response = urllib.request.urlopen(req, timeout=400)
                xbmc.log("AmpachePlugin::handle_request: nossl",xbmc.LOGDEBUG)
        except urllib.error.HTTPError as e:
            xbmc.log("AmpachePlugin::handle_request: HTTPError, reason " + e.reason ,xbmc.LOGDEBUG)
            xbmc.executebuiltin("ConnectionError" )
            raise self.ConnectionError
        except urllib.error.URLError as e:
            xbmc.log("AmpachePlugin::handle_request: URLError, reason " + e.reason,xbmc.LOGDEBUG)
            xbmc.executebuiltin("ConnectionError" )
            raise self.ConnectionError
        except:
            xbmc.log("AmpachePlugin::handle_request: ConnectionError",xbmc.LOGDEBUG)
            xbmc.executebuiltin("ConnectionError" )
            raise self.ConnectionError
        headers = response.headers
        contents = response.read()
        response.close()
        try:
            strCont = contents.decode()
            xbmc.log("AmpachePlugin::handle_request: Contents " + strCont,xbmc.LOGDEBUG)
        except:
            pass
        return headers,contents

    def AMPACHECONNECT(self):
        version = 350001
        socket.setdefaulttimeout(3600)
        nTime = int(time.time())
        use_api_key = self._connectionData["use_api_key"]
        if utils.strBool_to_bool(use_api_key):
            xbmc.log("AmpachePlugin::AMPACHECONNECT api_key",xbmc.LOGDEBUG)
            myURL = self.get_auth_key_login_url()
        else: 
            xbmc.log("AmpachePlugin::AMPACHECONNECT login password",xbmc.LOGDEBUG)
            myURL = self.get_user_pwd_login_url(nTime)
        try:
            headers,contents = self.handle_request(myURL)
        except self.ConnectionError:
            xbmc.log("AmpachePlugin::AMPACHECONNECT ConnectionError",xbmc.LOGDEBUG)
            raise self.ConnectionError
        xbmc.log("AmpachePlugin::AMPACHECONNECT ConnectionOk",xbmc.LOGDEBUG)
        tree=ET.XML(contents)
        errormess = tree.findtext('error')
        if errormess:
            errornode = tree.find("error")
            if errornode.attrib["code"]=="401":
                if "time" in errormess:
                    xbmc.executebuiltin("Notification(Error,If you are using Nextcloud don't check api_key box)")
                else:
                    xbmc.executebuiltin("Notification(Error,Connection error)")
            raise self.ConnectionError
            return
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
        self._ampache.setSetting("playlists", tree.findtext("playlists"))
        self._ampache.setSetting("add", tree.findtext("add"))
        self._ampache.setSetting("token", token)
        self._ampache.setSetting("token-exp", str(nTime+24000))
        return

    def ampache_http_request(self,action):
        thisURL = self.build_ampache_url(action)
        try:
            headers,contents  = self.handle_request(thisURL)
        except self.ConnectionError:
            raise self.ConnectionError
        if PY2:
            contents = contents.replace("\0", "")
        #parser = ET.XMLParser(recover=True)
        #tree=ET.XML(contents, parser = parser)
        tree=ET.XML(contents)
        if tree.findtext("error"):
            errornode = tree.find("error")
            if errornode.attrib["code"]=="401":
                try:
                    self.AMPACHECONNECT()
                except self.ConnectionError:
                    raise self.ConnectionError
                thisURL = self.build_ampache_url(action)
                try:
                    headers,contents = self.handle_request(thisURL)
                except self.ConnectionError:
                    raise self.ConnectionError
                tree=ET.XML(contents)
        return tree
    
    def build_ampache_url(self,action):
        if utils.check_tokenexp():
            xbmc.log("refreshing token...", xbmc.LOGDEBUG )
            try:
                self.AMPACHECONNECT()
            except:
                return
        token = self._ampache.getSetting("token")
        thisURL = self._connectionData["url"] + '/server/xml.server.php?action=' + action 
        thisURL += '&auth=' + token
        thisURL += '&limit=' +str(self.limit)
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

