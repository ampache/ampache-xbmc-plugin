from future.utils import PY2
import re
import os
import xbmc,xbmcaddon

from resources.lib import ampache_connect

ampache = xbmcaddon.Addon()

user_dir = xbmc.translatePath( ampache.getAddonInfo('profile'))
if PY2:
    user_dir = user_dir.decode('utf-8')
user_mediaDir = os.path.join( user_dir , 'media' )
cacheDir = os.path.join( user_mediaDir , 'cache' )

def cacheArt(url):
    strippedAuth = url.split('&')
    imageID = re.search(r"id=(\d+)", strippedAuth[0])
    #security check:
    #also nexcloud server doesn't send images
    if imageID == None:
        raise NameError
    
    imageNamePng = imageID.group(1) + ".png"
    imageNameJpg = imageID.group(1) + ".jpg"
    pathPng = os.path.join( cacheDir , imageNamePng )
    pathJpg = os.path.join( cacheDir , imageNameJpg )
    if os.path.exists( pathPng ):
            #xbmc.log("AmpachePlugin::CacheArt: png cached",xbmc.LOGDEBUG)
            return pathPng
    elif os.path.exists( pathJpg ):
            #xbmc.log("AmpachePlugin::CacheArt: jpg cached",xbmc.LOGDEBUG)
            return pathJpg
    else:
            ampacheConnect = ampache_connect.AmpacheConnect()
            #xbmc.log("AmpachePlugin::CacheArt: File needs fetching ",xbmc.LOGDEBUG)
            headers,contents = ampacheConnect.handle_request(url)
            extension = headers['content-type']
            tmpExt = extension.split("/")
            if tmpExt[0] == 'image':
                    if tmpExt[1] == "jpeg":
                            fname = imageNameJpg
                    else:
                            fname = imageID.group(1) + '.' + tmpExt[1]
                    pathJpg = os.path.join( cacheDir , fname )
                    open( pathJpg, 'wb').write(contents)
                    #xbmc.log("AmpachePlugin::CacheArt: Cached " + str(fname), xbmc.LOGDEBUG )
                    return pathJpg
            else:
                    xbmc.log("AmpachePlugin::CacheArt: It didnt work", xbmc.LOGDEBUG )
                    raise NameError
                    #return False

def get_artLabels(albumArt):
    art_labels = {
            'banner' : albumArt, 
            'thumb': albumArt, 
            'icon': albumArt,
            'fanart': albumArt
            }
    return art_labels

def get_art(node):
    try:
        albumArt = cacheArt(node.findtext("art"))
    except NameError:
        albumArt = "DefaultFolder.png"
    #xbmc.log("AmpachePlugin::get_art: albumArt - " + str(albumArt), xbmc.LOGDEBUG )
    return albumArt


