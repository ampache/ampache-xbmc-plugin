from future.utils import PY2
import xbmc
import os
import xbmcaddon
 
ampache = xbmcaddon.Addon()

def clean_cache():
    base_dir = xbmc.translatePath( ampache.getAddonInfo('profile'))
    if PY2:
        base_dir = base_dir.decode('utf-8')
    #hack to force the creation of profile directory if don't exists
    if not os.path.isdir(base_dir):
        ampache.setSetting("api-version","350001")
    mediaDir = os.path.join( base_dir , 'media' )
    cacheDir = os.path.join( mediaDir , 'cache' )

    #if cacheDir doesn't exist, create it
    if not os.path.isdir(mediaDir):
        os.mkdir(mediaDir)
        if not os.path.isdir(cacheDir):
            os.mkdir(cacheDir)
    extensions = ('.png', '.jpg')

    #clean cache on start
    for currentFile in os.listdir(cacheDir):
        #xbmc.log("Clear Cache Art " + str(currentFile),xbmc.LOGDEBUG)
        pathDel = os.path.join( cacheDir, currentFile)
        os.remove(pathDel)


if __name__ == '__main__':
    clean_cache()
