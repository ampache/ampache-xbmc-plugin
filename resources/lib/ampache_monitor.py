import xbmc
import xbmcaddon

#service class
ampache = xbmcaddon.Addon("plugin.audio.ampache")

#from utils import get_objectId_from_fileURL

class AmpacheMonitor( xbmc.Monitor ):

    onPlay = False

    def __init__(self):
        xbmc.log( 'AmpacheMonitor::ServiceMonitor called', xbmc.LOGDEBUG)

    # start mainloop
    def run(self):
        while not self.abortRequested():
            if self.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

    def close(self):
        pass

    def onNotification(self, sender, method, data):
        #i don't know why i have called monitor.onNotification, but now it
        #seems useless
        #xbmc.Monitor.onNotification(self, sender, method, data)
        xbmc.log('AmpacheMonitor:Notification %s from %s, params: %s' % (method, sender, str(data)))

        #a little hack to avoid calling rate every time a song start
        if method == 'Player.OnStop':
            self.onPlay = False
        if method == 'Player.OnPlay':
            self.onPlay = True
        #called on infoChanged ( rating )
        if method == 'Info.OnChanged' and self.onPlay:
            #call setRating
            if xbmc.Player().isPlaying():
                try:
                    file_url = xbmc.Player().getPlayingFile()
                    #it is not our file
                    if not (self.get_objectId_from_fileURL( file_url )):
                        return
                except:
                    xbmc.log("AmpacheMonitor::no playing file " , xbmc.LOGDEBUG)
                    return
                xbmc.executebuiltin('RunPlugin(plugin://plugin.audio.ampache/?mode=205)')

    def get_objectId_from_fileURL( self,file_url ):
        params = get_params(file_url)
        object_id = None
        #i use two kind of object_id, i don't know, but sometime i have different
        #url, btw, no problem, i handle both and i solve the problem in this way
        try:
                object_id=params["object_id"]
                xbmc.log("AmpachePlugin::object_id " + object_id, xbmc.LOGDEBUG)
        except:
                pass
        try:
                object_id=params["oid"]
                xbmc.log("AmpachePlugin::object_id " + object_id, xbmc.LOGDEBUG)
        except:
                pass
        return object_id
