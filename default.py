from future import standard_library
from future.utils import PY2
standard_library.install_aliases()
from builtins import str
from builtins import range
import sys
import os
import random,xbmcplugin,xbmcgui,urllib.request,urllib.parse,urllib.error
import xml.etree.ElementTree as ET
import xbmcaddon

from resources.lib import ampache_connect
from resources.lib import servers_manager
from resources.lib import gui
from resources.lib import utils as ut
from resources.lib import art

# Shared resources

#addon name : plugin.audio.ampache
#do not use xbmcaddon.Addon() to avoid crashes when kore app is used ( it is
#possible to start a song without initialising the plugin
ampache = xbmcaddon.Addon("plugin.audio.ampache")

#ampache_addon_path =  ampache.getAddonInfo('path')
#ampache_dir = xbmc.translatePath( ampache_addon_path )
#if PY2:
#    ampache_dir = ampache_dir.decode('utf-8')
#BASE_RESOURCE_PATH = os.path.join( ampache_dir, 'resources' )
#mediaDir = os.path.join( BASE_RESOURCE_PATH , 'media' )
#imagepath = os.path.join( mediaDir ,'images')

def searchGui():
    dialog = xbmcgui.Dialog()
    ret = dialog.contextmenu([ut.tString(30106),ut.tString(30107),ut.tString(30108),\
                              ut.tString(30109),ut.tString(30110),ut.tString(30111)])
    endDir = False
    if ret == 0:
        endDir = do_search("artists")
    elif ret == 1:
        endDir = do_search("albums")
    elif ret == 2:
        endDir = do_search("songs")
    elif ret == 3:
        endDir = do_search("playlists")
    elif ret == 4:
        endDir = do_search("songs","search_songs")
    elif ret == 5:
        ret2 = dialog.contextmenu([ut.tString(30112),ut.tString(30113),ut.tString(30114)])
        if ret2 == 0:
            endDir = do_search("tags","tag_artists")
        elif ret2 == 1:
            endDir = do_search("tags","tag_albums")
        elif ret2 == 2:
            endDir = do_search("tags","tag_songs")

    return endDir

#return album and artist name, only album could be confusing
def get_album_artist_name(node):
    fullname = node.findtext("name").encode("utf-8")
    if PY2:
        fullname += " - "
    else:
        fullname += b" - "
    fullname += node.findtext("artist").encode("utf-8")
    return fullname

def get_infolabels(object_type , node):
    infoLabels = None
    avgRating = node.findtext("averagerating")
    if avgRating:
        avgRating = int(float(avgRating)*2)
    else:
        avgRating = 0
    if object_type == 'albums':
        infoLabels = {
            'Title' : str(node.findtext("name")) ,
            'Album' : str(node.findtext("name")) ,
            'Artist' : str(node.findtext("artist")),
            'Discnumber' : str(node.findtext("disk")),
            'Year' : node.findtext("year") ,
            'UserRating' : avgRating,
            'Mediatype' : 'album'
        }
 
    elif object_type == 'artists':
        
        infoLabels = {
            'Title' : str(node.findtext("name")) ,
            'Artist' : str(node.findtext("name")),
            'UserRating' : avgRating,
            'Mediatype' : 'artist'
        }

    elif object_type == 'songs':
        infoLabels = {
            'Title' : str(node.findtext("title")) ,
            'Artist' : str(node.findtext("artist")),
            'Album' :  str(node.findtext("album")),
            'Size' : node.findtext("size") ,
            'Duration' : node.findtext("time"),
            'Year' : node.findtext("year") ,
            'Tracknumber' : node.findtext("track"),
            'UserRating' : avgRating,
            'Mediatype' : 'song'
        }

    return infoLabels

#handle albumArt and song info
def fillListItemWithSongInfo(liz,node):
    albumArt = art.get_art(node)
    liz.setLabel(str(node.findtext("title")))
    liz.setArt( art.get_artLabels(albumArt) )
    #needed by play_track to play the song, added here to uniform api
    liz.setPath(node.findtext("url"))
    liz.setInfo( type="music", infoLabels=get_infolabels("songs", node) )
    liz.setMimeType(node.findtext("mime"))

# Used to populate items for songs on XBMC. Calls plugin script with mode == 9 and object_id == (ampache song id)
# TODO: Merge with addDir(). Same basic idea going on, this one adds links all at once, that one does it one at a time
#       Also, some property things, some different context menu things.
def addSongLinks(elem):
   
    #win_id is necessary to avoid problems in musicplaylist window, where this
    #script doesn't work
    curr_win_id = xbmcgui.getCurrentWindowId()
    xbmcplugin.setContent(int(sys.argv[1]), "songs")
    ok=True
    it=[]
    for node in elem.iter("song"):
        liz=xbmcgui.ListItem()
        fillListItemWithSongInfo(liz,node)
        liz.setProperty("IsPlayable", "true")

        cm = []
        try:
            artist_elem = node.find("artist")
            artist_id = int(artist_elem.attrib["id"])
            cm.append( ( ut.tString(30138),
            "Container.Update(%s?object_id=%s&mode=15&win_id=%s)" % (
                sys.argv[0],artist_id, curr_win_id ) ) )
        except:
            pass
        
        try:
            album_elem = node.find("album")
            album_id = int(album_elem.attrib["id"])
            cm.append( ( ut.tString(30139),
            "Container.Update(%s?object_id=%s&mode=16&win_id=%s)" % (
                sys.argv[0],album_id, curr_win_id ) ) )
        except:
            pass
        
        try:
            song_elem = node.find("song")
            song_title = str(node.findtext("title"))
            cm.append( ( ut.tString(30140),
            "Container.Update(%s?title=%s&mode=17&win_id=%s)" % (
                sys.argv[0],song_title, curr_win_id ) ) )
        except:
            pass

        if cm != []:
            liz.addContextMenuItems(cm)

        song_url = node.findtext("url")
        song_id = int(node.attrib["id"])
        track_parameters = { "mode": 45, "song_url" : song_url, "object_id" : song_id}
        url = sys.argv[0] + '?' + urllib.parse.urlencode(track_parameters)
        tu= (url,liz)
        it.append(tu)
    
    ok=xbmcplugin.addDirectoryItems(handle=int(sys.argv[1]),items=it,totalItems=len(elem))
    #@xbmc.log("AmpachePlugin::addSongLinks " + str(ok), xbmc.LOGDEBUG)
    return ok

# The function that actually plays an Ampache URL by using setResolvedUrl. 
def play_track(object_id,song_url):
    if song_url == None or object_id == None:
        xbmc.log("AmpachePlugin::play_track object or song null", xbmc.LOGNOTICE )
        return

    old_object_id = None

    #check if we need the song infolabels ( object_id cached is different from
    #object_id of the song, for instance as kore app call the song
    try:
            plugin_url = xbmc.getInfoLabel('ListItem.FileNameAndPath')
            params=ut.get_params(plugin_url)
            old_object_id=int(params["object_id"])
            xbmc.log("AmpachePlugin::play_track old_object_id " + str(old_object_id), xbmc.LOGDEBUG)
    except:
            pass

    liz = xbmcgui.ListItem()
    try:
        if old_object_id == None or old_object_id != object_id:
            ampConn = ampache_connect.AmpacheConnect()
            xbmc.log("AmpachePlugin::play_track refresh infoLabels", xbmc.LOGDEBUG)
            ampConn.filter = object_id
            elem = ampConn.ampache_http_request("song")
            for thisnode in elem:
                node = thisnode
            fillListItemWithSongInfo(liz,node)
            liz.setProperty("IsPlayable", "true")
    except:
        pass

    liz.setPath(song_url)
    #rating = xbmc.getInfoLabel('ListItem.UserRating')
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True,listitem=liz)

# Main function for adding xbmc plugin elements
def addDir(name,object_id,mode,iconImage=None,elem=None,infoLabels=None):
    if iconImage == None:
        iconImage = "DefaultFolder.png"
    
    if infoLabels == None:
        infoLabels={ "Title": name }
    
    liz=xbmcgui.ListItem(name)
    liz.setInfo( type="Music", infoLabels=infoLabels )
    liz.setArt(  art.get_artLabels(iconImage) )
    liz.setProperty('IsPlayable', 'false')

    try:
        artist_elem = elem.find("artist")
        artist_id = int(artist_elem.attrib["id"]) 
        cm = []
        cm.append( ( ut.tString(30141), "Container.Update(%s?object_id=%s&mode=2)" % ( sys.argv[0],artist_id ) ) )
        liz.addContextMenuItems(cm)
    except:
        pass

    handle=int(sys.argv[1])

    u=sys.argv[0]+"?object_id="+str(object_id)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)
    xbmc.log("AmpachePlugin::addDir url " + u, xbmc.LOGDEBUG)
    ok=xbmcplugin.addDirectoryItem(handle=handle,url=u,listitem=liz,isFolder=True)
    #xbmc.log("AmpachePlugin::addDir ok " + str(ok), xbmc.LOGDEBUG)
    return ok

#catch all function to add items to the directory using the low level addDir
#or addSongLinks functions
def addItem( object_type, mode , elem, useCacheArt=True):
    image = "DefaultFolder.png"
    xbmc.log("AmpachePlugin::addItem: object_type - " + str(object_type) , xbmc.LOGDEBUG )
    if object_type == 'albums':
        allid = set()
        for node in elem.iter('album'):
            #no unicode function, cause urllib quot_plus error ( bug )
            album_id = int(node.attrib["id"])
            #remove duplicates in album names ( workaround for a problem in server comunication )
            if album_id not in allid:
                allid.add(album_id)
            else:
                continue
            fullname = get_album_artist_name(node)
            if useCacheArt:
                image = art.get_art(node)
            addDir(fullname,node.attrib["id"],mode,image,node,infoLabels=get_infolabels("albums",node))
    elif object_type == 'artists':
        for node in elem.iter('artist'):
            addDir(node.findtext("name").encode("utf-8"),node.attrib["id"],mode,image,node,infoLabels=get_infolabels("artists",node))
    elif object_type == 'playlists':
        for node in elem.iter('playlist'):
            addDir(node.findtext("name").encode("utf-8"),node.attrib["id"],mode,image,node)
    elif object_type == 'tags':
        for node in elem.iter('tag'):
            addDir(node.findtext("name").encode("utf-8"),node.attrib["id"],mode,image,node)
    elif object_type == 'songs':
        addSongLinks(elem)

def get_all(object_type):
    limit = int(ampache.getSetting(object_type))
    step = 500
    for offset in range( 0, limit, step):
        newLimit = offset+step
        get_items(object_type, limit=step, offset=offset,
                useCacheArt=False)


def get_items(object_type, object_id=None, add=None,\
        thisFilter=None,limit=5000,useCacheArt=True, object_subtype=None,\
        exact=None, offset=None ):
    
    if object_type:
        xbmc.log("AmpachePlugin::get_items: object_type " + object_type, xbmc.LOGDEBUG)
    else:
        #should be not possible
        xbmc.log("AmpachePlugin::get_items: object_type set to None" , xbmc.LOGDEBUG)
        return

    if object_subtype:
        xbmc.log("AmpachePlugin::get_items: object_subtype " + object_subtype, xbmc.LOGDEBUG)
    if object_id:
        xbmc.log("AmpachePlugin::get_items: object_id " + str(object_id), xbmc.LOGDEBUG)

    if limit == None:
        limit = int(ampache.getSetting(object_type))
    mode = None

    xbmcplugin.setContent(int(sys.argv[1]), object_type)
    #default: object_type is the action,otherwise see the if list below
    action = object_type
    
    #do not use action = object_subtype cause in tags it is used only to
    #discriminate between subtypes
    if object_type == 'albums':
        if object_subtype == 'artist_albums':
            action = 'artist_albums'
            addDir("All Songs",object_id,12)
        elif object_subtype == 'tag_albums':
            action = 'tag_albums'
        elif object_subtype == 'album':
            action = 'album'
    elif object_type == 'artists':
        if object_subtype == 'tag_artists':
            action = 'tag_artists'
        if object_subtype == 'artist':
            action = 'artist'
    elif object_type == 'songs':
        if object_subtype == 'tag_songs':
            action = 'tag_songs'
        elif object_subtype == 'playlist_songs':
            action = 'playlist_songs'
        elif object_subtype == 'album_songs':
            action = 'album_songs'
        elif object_subtype == 'artist_songs':
            action = 'artist_songs'
        elif object_subtype == 'search_songs':
            action = 'search_songs'

    if object_id:
        thisFilter = object_id
    
    try:
        ampConn = ampache_connect.AmpacheConnect()
        ampConn.add = add
        ampConn.filter = thisFilter
        ampConn.limit = limit
        ampConn.exact = exact
        ampConn.offset = offset

        elem = ampConn.ampache_http_request(action)
    except:
        return

    #after the request, set the mode 

    if object_type == 'artists':
        mode = 2
    elif object_type == 'albums':
        mode = 3
    elif object_type == 'playlists':
        mode = 14
    elif object_type == 'tags':
        if object_subtype == 'tag_artists':
            mode = 19
        elif object_subtype == 'tag_albums':
            mode = 20
        elif object_subtype == 'tag_songs':
            mode = 21

    addItem( object_type, mode , elem, useCacheArt)

def do_search(object_type,object_subtype=None,thisFilter=None):
    if not thisFilter:
        thisFilter = gui.getFilterFromUser()
    if thisFilter:
        get_items(object_type=object_type,thisFilter=thisFilter,object_subtype=object_subtype)
        return True
    return False

def get_stats(object_type, object_subtype=None, limit=5000 ):       
    
    ampConn = ampache_connect.AmpacheConnect()
    
    xbmc.log("AmpachePlugin::get_stats ",  xbmc.LOGDEBUG)
    mode = None
    if object_type == 'artists':
        mode = 2
    elif object_type == 'albums':
        mode = 3
   
    xbmcplugin.setContent(int(sys.argv[1]), object_type)

    action = 'stats'
    if(int(ampache.getSetting("api-version"))) < 400001:
        amtype = object_subtype
        thisFilter = None
    else:
        if object_type == 'albums':
            amtype='album'
        elif object_type == 'artists':
            amtype='artist'
        elif object_type == 'songs':
            amtype='song'
        thisFilter = object_subtype
    
    try:
        ampConn.filter = thisFilter
        ampConn.limit = limit
        ampConn.type = amtype
                
        elem = ampConn.ampache_http_request(action)
    except:
        return
  
    addItem( object_type, mode , elem)

def get_recent(object_type,object_id,object_subtype=None):   

    if object_id == 9999998:
        update = ampache.getSetting("add")
        xbmc.log(update[:10],xbmc.LOGNOTICE)
        get_items(object_type=object_type,add=update[:10],object_subtype=object_subtype)
    elif object_id == 9999997:
        get_items(object_type=object_type,add=ut.get_time(-7),object_subtype=object_subtype)
    elif object_id == 9999996:
        get_items(object_type=object_type,add=ut.get_time(-30),object_subtype=object_subtype)
    elif object_id == 9999995:
        get_items(object_type=object_type,add=ut.get_time(-90),object_subtype=object_subtype)

def get_random(object_type):
    xbmc.log("AmpachePlugin::get_random: object_type " + object_type, xbmc.LOGDEBUG)
    mode = None
    #object type can be : albums, artists, songs, playlists
    
    ampConn = ampache_connect.AmpacheConnect()
    
    if object_type == 'albums':
        amtype='album'
        mode = 3
    elif object_type == 'artists':
        amtype='artist'
        mode = 2
    elif object_type == 'playlists':
        amtype='playlist'
        mode = 14
    elif object_type == 'songs':
        amtype='song'
    
    xbmcplugin.setContent(int(sys.argv[1]), object_type)
        
    random_items = (int(ampache.getSetting("random_items"))*3)+3
    xbmc.log("AmpachePlugin::get_random: random_items " + str(random_items), xbmc.LOGDEBUG )
    items = int(ampache.getSetting(object_type))
    xbmc.log("AmpachePlugin::get_random: total items in the catalog " + str(items), xbmc.LOGDEBUG )
    if random_items > items:
        #if items are less than random_itmes, return all items
        get_items(object_type, limit=items)
        return
    #playlists are not in the new stats api, so, use the old mode
    if(int(ampache.getSetting("api-version"))) >= 400001 and object_type != 'playlists':
        action = 'stats'
        thisFilter = 'random'
        try:
            ampConn.filter = thisFilter
            ampConn.limit = random_items
            ampConn.type = amtype

            elem = ampConn.ampache_http_request(action)
            addItem( object_type, mode , elem)
        except:
            return
    
    else: 
        seq = random.sample(range(items),random_items)
        xbmc.log("AmpachePlugin::get_random: seq " + str(seq), xbmc.LOGDEBUG )
        elements = []
        for item_id in seq:
            try:
                ampConn.offset = item_id
                ampConn.limit = 1
                elem = ampConn.ampache_http_request(object_type)
                elements.append(elem)
            except:
                pass
   
        for el in elements:
            addItem( object_type, mode , el)

if (__name__ == '__main__'):

    name=None
    mode=None
    object_id=None
    win_id=None
    title=None
    song_url=None

    handle = int(sys.argv[1])
    plugin_url=sys.argv[2]

    params=ut.get_params(plugin_url)
    xbmc.log("AmpachePlugin::init handle: " + str(handle) + " url: " + plugin_url, xbmc.LOGDEBUG)

    try:
            name=urllib.parse.unquote_plus(params["name"])
            xbmc.log("AmpachePlugin::name " + name, xbmc.LOGDEBUG)
    except:
            pass
    try:
            mode=int(params["mode"])
            xbmc.log("AmpachePlugin::mode " + str(mode), xbmc.LOGDEBUG)
    except:
            pass
    try:
            object_id=int(params["object_id"])
            xbmc.log("AmpachePlugin::object_id " + str(object_id), xbmc.LOGDEBUG)
    except:
            pass
    try:
            win_id=int(params["win_id"])
            xbmc.log("AmpachePlugin::win_id " + str(win_id), xbmc.LOGDEBUG)
    except:
            pass
    try:
            title=urllib.parse.unquote_plus(params["title"])
            xbmc.log("AmpachePlugin::title " + title, xbmc.LOGDEBUG)
    except:
            pass
    try:
            song_url=urllib.parse.unquote_plus(params["song_url"])
            xbmc.log("AmpachePlugin::song_url " + song_url, xbmc.LOGDEBUG)
    except:
            pass

    servers_manager.initializeServer()
    
    ampacheConnect = ampache_connect.AmpacheConnect()

    #check if the connection is expired
    #initialisation
    if mode==None or ut.check_tokenexp():
        try:
            ampacheConnect.AMPACHECONNECT()
        except:
            pass

    #start menu
    if mode==None:
        addDir(ut.tString(30101),None,4)
        addDir(ut.tString(30102),None,25)
        addDir(ut.tString(30103),None,23)
        addDir(ut.tString(30104),None,24)
        addDir(ut.tString(30023),None,44)
        addDir(ut.tString(30105),None,40)
        
    #   artist list ( called from main screen  ( mode None ) , search
    #   screen ( mode 4 ) and recent ( mode 5 )  )

    elif mode==1:
        #artist, album, songs, playlist follow the same structure
        #search function
        num_items = (int(ampache.getSetting("random_items"))*3)+3
        #get all artists
        if object_id == None:
            get_all("artists")
            #get_items("artists", limit=None, useCacheArt=False)
        elif object_id == 9999999:
            endDir = do_search("artists")
            if endDir == False:
                #no end directory item
                mode = 100
        #recent function
        elif object_id > 9999994 and object_id < 9999999:
            get_recent( "artists", object_id )
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999994,2,os.path.join(imagepath,'refresh_icon.png'))
            get_random('artists')
        elif object_id == 9999993:
            get_stats(object_type="artists",object_subtype="hightest",limit=num_items)
        elif object_id == 9999992:
            get_stats(object_type="artists",object_subtype="frequent",limit=num_items)
        elif object_id == 9999991:
            get_stats(object_type="artists",object_subtype="flagged",limit=num_items)
        elif object_id == 9999990:
            get_stats(object_type="artists",object_subtype="forgotten",limit=num_items)
        elif object_id == 9999989:
            get_stats(object_type="artists",object_subtype="newest",limit=num_items)
           
    #   albums list ( called from main screen ( mode None ) , search
    #   screen ( mode 4 ) and recent ( mode 5 )

    elif mode==2:
        num_items = (int(ampache.getSetting("random_items"))*3)+3
        #get all albums
        if object_id == None:
            get_all("albums")
            #get_items("albums", limit=None, useCacheArt=False)
        elif object_id == 9999999:
            endDir = do_search("albums")
            if endDir == False:
                #no end directory item
                mode = 100
        elif object_id > 9999994 and object_id < 9999999:
            get_recent( "albums", object_id )
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999990,2,os.path.join(imagepath, 'refresh_icon.png'))
            get_random('albums')
        elif object_id == 9999993:
            get_stats(object_type="albums",object_subtype="hightest",limit=num_items)
        elif object_id == 9999992:
            get_stats(object_type="albums",object_subtype="frequent",limit=num_items)
        elif object_id == 9999991:
            get_stats(object_type="albums",object_subtype="flagged",limit=num_items)
        elif object_id == 9999990:
            get_stats(object_type="albums",object_subtype="forgotten",limit=num_items)
        elif object_id == 9999989:
            get_stats(object_type="albums",object_subtype="newest",limit=num_items)
        elif object_id:
            get_items(object_type="albums",object_id=object_id,object_subtype="artist_albums")

    #   song mode ( called from search screen ( mode 4 ) and recent ( mode 5 )  )
            
    elif mode==3:
        num_items = (int(ampache.getSetting("random_items"))*3)+3
        if object_id > 9999994 and object_id < 9999999:
            get_recent( "songs", object_id )
        elif object_id == 9999999:
            endDir = do_search("songs")
            if endDir == False:
                #no end directory item
                mode = 100
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999994,2,os.path.join(imagepath, 'refresh_icon.png'))
            get_random('songs')
        elif object_id == 9999993:
            get_stats(object_type="songs",object_subtype="hightest",limit=num_items)
        elif object_id == 9999992:
            get_stats(object_type="songs",object_subtype="frequent",limit=num_items)
        elif object_id == 9999991:
            get_stats(object_type="songs",object_subtype="flagged",limit=num_items)
        elif object_id == 9999990:
            get_stats(object_type="songs",object_subtype="forgotten",limit=num_items)
        elif object_id == 9999989:
            get_stats(object_type="songs",object_subtype="newest",limit=num_items)
        else:
            get_items(object_type="songs",object_id=object_id,object_subtype="album_songs")

    # search screen ( called from main screen )

    elif mode==4:
        if not (ut.strBool_to_bool(ampache.getSetting("old-search-gui"))):
            endDir = searchGui()
            if endDir == False:
                #no end directory item
                mode = 100
        else:
            addDir(ut.tString(30120),9999999,1)
            addDir(ut.tString(30121),9999999,2)
            addDir(ut.tString(30122),9999999,3)
            addDir(ut.tString(30123),9999999,13)
            addDir(ut.tString(30124),9999999,11)
            addDir(ut.tString(30125),9999999,18)

    # recent additions screen ( called from main screen )

    elif mode==5:
        addDir(ut.tString(30126),9999998,6)
        addDir(ut.tString(30127),9999997,6)
        addDir(ut.tString(30128),9999996,6)
        addDir(ut.tString(30129),9999995,6)

    #   screen with recent time possibilities ( subscreen of recent artists,
    #   recent albums, recent songs ) ( called from mode 5 )

    elif mode==6:
        #not clean, but i don't want to change too much the old code
        if object_id > 9999995:
            #object_id for playlists is 9999995 so 9999999-object_id is 4 that is search mode
            #i have to use another method, so i use the hardcoded mode number (13)
            mode_new = 9999999-object_id
        elif object_id == 9999995:
            mode_new = 13
        
        addDir(ut.tString(30130),9999998,mode_new)
        addDir(ut.tString(30131),9999997,mode_new)
        addDir(ut.tString(30132),9999996,mode_new)
        addDir(ut.tString(30133),9999995,mode_new)

    # general random mode screen ( called from main screen )

    elif mode==7:
        addDir(ut.tString(30134),9999994,1)
        addDir(ut.tString(30135),9999994,2)
        addDir(ut.tString(30136),9999994,3)
        addDir(ut.tString(30137),9999994,13)

    #old mode 
    #
    #random mode screen ( display artists, albums or songs ) ( called from mode
    #   7  )
    #elif mode==8:
    #end old mode

    # mode 11 : search all
    elif mode==11:
        endDir = do_search("songs","search_songs")
        if endDir == False:
            #no end directory item
            mode = 100

    # mode 12 : artist_songs
    elif mode==12:
        get_items(object_type="songs",object_id=object_id,object_subtype="artist_songs" )

    #   playlist full list ( called from main screen )

    elif mode==13:
        if object_id == None:
            get_all("playlists")
            #get_items(object_type="playlists")
        elif object_id == 9999999:
            endDir = do_search("playlists")
            if endDir == False:
                #no end directory item
                mode = 100
        elif object_id > 9999994 and object_id < 9999999:
            get_recent( "playlists", object_id )
        elif object_id == 9999994:
            #removed cause nasty recursive call using some commands in web interface
            #addDir("Refresh..",9999994,2,os.path.join(imagepath, 'refresh_icon.png'))
            get_random('playlists')
        elif object_id:
            get_items(object_type="playlists",object_id=object_id)

    #   playlist song mode

    elif mode==14:
        get_items(object_type="songs",object_id=object_id,object_subtype="playlist_songs")

    elif mode==15:
        if xbmc.getCondVisibility("Window.IsActive(musicplaylist)"):
            xbmc.executebuiltin("ActivateWindow(%s)" % (win_id,))
        get_items(object_type="artists",object_id=object_id,object_subtype="artist")

    elif mode==16:
        if xbmc.getCondVisibility("Window.IsActive(musicplaylist)"):
            xbmc.executebuiltin("ActivateWindow(%s)" % (win_id,))
        get_items(object_type="albums",object_id=object_id,object_subtype="album")

    elif mode==17:
        if xbmc.getCondVisibility("Window.IsActive(musicplaylist)"):
            xbmc.executebuiltin("ActivateWindow(%s)" % (win_id,))
        endDir = do_search("songs",thisFilter=title)
        if endDir == False:
            #no end directory item
            mode = 100

    #tags
    elif mode==18:
        addDir(ut.tString(30142),object_id,19)
        addDir(ut.tString(30143),object_id,20)
        addDir(ut.tString(30144),object_id,21)

    elif mode==19:
        if object_id == 9999999:
            endDir = do_search("tags","tag_artists")
            if endDir == False:
                #no end directory item
                mode = 100
        elif object_id:
            get_items(object_type="artists", object_subtype="tag_artists",object_id=object_id)
        else:
            get_items(object_type = "tags", object_subtype="tag_artists")

    elif mode==20:
        if object_id == 9999999:
            endDir = do_search("tags","tag_albums")
            if endDir == False:
                #no end directory item
                mode = 100
        elif object_id:
            get_items(object_type="albums", object_subtype="tag_albums",object_id=object_id)
        else:
            get_items(object_type = "tags", object_subtype="tag_albums")

    elif mode==21:
        if object_id == 9999999:
            endDir = do_search("tags","tag_songs")
            if endDir == False:
                #no end directory item
                mode = 100
        elif object_id:
            get_items(object_type="songs", object_subtype="tag_songs",object_id=object_id)
        else:
            get_items(object_type = "tags", object_subtype="tag_songs")

    #Quick access
    elif mode==23:
        addDir(ut.tString(30145),None,5)
        addDir(ut.tString(30146),None,7)
        if(int(ampache.getSetting("api-version"))) >= 400001:
            addDir(ut.tString(30148),9999993,30)
            addDir(ut.tString(30164),9999992,31)
            addDir(ut.tString(30165),9999991,32)
            addDir(ut.tString(30166),9999990,33)
            addDir(ut.tString(30167),9999989,34)

    #Library
    elif mode==24:
        addDir(ut.tString(30115) +" (" + ampache.getSetting("artists")+ ")",None,1)
        addDir(ut.tString(30116) + " (" + ampache.getSetting("albums") + ")",None,2)
        addDir(ut.tString(30118) + " (" + ampache.getSetting("playlists")+ ")",None,13)
        apiVersion = int(ampache.getSetting("api-version"))
        if(apiVersion < 400003 and apiVersion >= 380001):
            addDir(ut.tString(30119),None,18)
    
    elif mode==25:
        addDir(ut.tString(30127),9999997,6)
        addDir(ut.tString(30135),9999994,2)
        if(int(ampache.getSetting("api-version"))) >= 400001:
            addDir(ut.tString(30162),9999989,2)
            addDir(ut.tString(30153),9999992,2)
        addDir(ut.tString(30147),9999994,3)

    #hightest
    elif mode==30:
        addDir(ut.tString(30149),9999993,1)
        addDir(ut.tString(30150),9999993,2)
        addDir(ut.tString(30151),9999993,3)

    #frequent
    elif mode==31:
        addDir(ut.tString(30152),9999992,1)
        addDir(ut.tString(30153),9999992,2)
        addDir(ut.tString(30154),9999992,3)
    
    #flagged
    elif mode==32:
        addDir(ut.tString(30155),9999991,1)
        addDir(ut.tString(30156),9999991,2)
        addDir(ut.tString(30157),9999991,3)

    #forgotten
    elif mode==33:
        addDir(ut.tString(30158),9999990,1)
        addDir(ut.tString(30159),9999990,2)
        addDir(ut.tString(30160),9999990,3)
    
    #newest
    elif mode==34:
        addDir(ut.tString(30161),9999989,1)
        addDir(ut.tString(30162),9999989,2)
        addDir(ut.tString(30163),9999989,3)
    
    elif mode==40:
        ampache.openSettings()

    elif mode==41:
        if servers_manager.addServer():
            servers_manager.switchServer()
    
    elif mode==42:
        if servers_manager.deleteServer():
            servers_manager.switchServer()
    
    elif mode==43:
        servers_manager.modifyServer()
    
    elif mode==44:
        servers_manager.switchServer()

    #play track mode  ( mode set in add_links function )
    #mode 45 to avoid endDirectory
    elif mode==45:
        play_track(object_id, song_url)

    if mode == None or mode < 40:
        xbmc.log("AmpachePlugin::endOfDirectory " + str(handle),  xbmc.LOGDEBUG)
        xbmcplugin.endOfDirectory(handle)
