import time
import datetime
import xbmcaddon

ampache = xbmcaddon.Addon()

def int_to_strBool(s):
    if s == 1:
        return 'true'
    elif s == 0:
        return 'false'
    else:
        raise ValueError

#   string to bool function : from string 'true' or 'false' to boolean True or
#   False, raise ValueError
def strBool_to_bool(s):
    if s == 'true':
        return True
    elif s == 'false':
        return False
    else:
        raise ValueError

def check_tokenexp():
    tokenexp = int(ampache.getSetting("token-exp"))
    if int(time.time()) > tokenexp:
        return True
    return False

def get_time(time_offset):
    d = datetime.date.today()
    dt = datetime.timedelta(days=time_offset)
    nd = d + dt
    return nd.isoformat()

#return the translated String
def tString(code):
    return ampache.getLocalizedString(code)

def get_params(plugin_url):
    param=[]
    paramstring=plugin_url
    if len(paramstring)>=2:
            params=plugin_url
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]

    return param
