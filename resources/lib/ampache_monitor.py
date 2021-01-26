import xbmc
import xbmcaddon

from art import clean_cache_art
 
ampache = xbmcaddon.Addon("plugin.audio.ampache")

class AmpacheMonitor( xbmc.Monitor ):

    onPlay = False

    def __init__(self):
        clean_cache_art()
        xbmc.log( 'AmpachePlugin::ServiceMonitor called', xbmc.LOGDEBUG)

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
        xbmc.log('AmpachePlugin::Notification %s from %s, params: %s' % (method, sender, str(data)))

        #a little hack to avoid calling rate every time a song start
        if method == 'Player.OnStop':
            self.onPlay = False
        if method == 'Player.OnPlay':
            self.onPlay = True
        #called on infoChanged ( rating )
        if method == 'Info.OnChanged' and self.onPlay:
            #call setRating
            if xbmc.Player().isPlaying():
                xbmc.executebuiltin('RunPlugin(plugin://plugin.audio.ampache/?mode=47)')


