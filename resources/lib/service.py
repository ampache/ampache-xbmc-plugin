import xbmc
import xbmcaddon

from art import clean_cache_art
 
ampache = xbmcaddon.Addon("plugin.audio.ampache")

class Main():

    def __init__(self):
        self.monitor = ServiceMonitor()

        # start mainloop
        self.main_loop()

    def main_loop(self):
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

    def close():
        pass

class ServiceMonitor( xbmc.Monitor ):

    onPlay = False

    def __init__( self, *args, **kwargs ):
        xbmc.log( 'AmpachePlugin::ServiceMonitor called', xbmc.LOGDEBUG)
        #pass

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

if __name__ == '__main__':
    clean_cache_art()
    Main()
