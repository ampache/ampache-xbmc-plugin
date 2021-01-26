import xbmc
import xbmcplugin

#main plugin library

class AmpachePlayer( xbmc.Player ):

    def __init__( self, *args ):
        pass
        
    def play( self, handle, liz ):
        xbmcplugin.setResolvedUrl(handle=handle, succeeded=True,listitem=liz)
        


