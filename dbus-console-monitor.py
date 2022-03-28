import dbus
import time
import os
from xml.etree import ElementTree


# === CONFIG ===
# DBus system services with paths that will be monitored.
# Leaved path empty to use auto discovery-feature
_ServicePathConfig = { 
     "com.victronenergy.pvinverter.pv_XB3250H8029021": ["/Serial"],
     "com.victronenergy.grid.http_40": []
}

# Blacklist will not output this paths when path autodiscovery feature is used
_BlacklistPathConfig = [
    "/ServiceMapping",
    "/Debug", 
    "/Buzzer", 
    "/Timer", 
    "/VebusService", 
    "/Mgmt", 
    "/Serial", 
    "/Firmware", 
    "/Relay/",
    "/Dvcc",
    "/Connected",
    "/Hub"
    ]
    
# refresh delay in seconds between each DBus querying
_RefreshSleep = 0.5 # 500ms



# === =========================== ===
# === NO CHANGES AFTER THIS POINT ===
# === =========================== ===



# === FUNCTIONS ===
def pathNames(bus,service,object_path="/",paths=None,blacklist=[]):
    result = []
    
    if paths == None:
        paths = {}
    paths[object_path] = {}
    obj = bus.get_object(service, object_path)
    iface = dbus.Interface(obj, 'org.freedesktop.DBus.Introspectable')
    xml_string = iface.Introspect()
    root = ElementTree.fromstring(xml_string)
    for child in root:
        if child.tag == 'node':
            if object_path == '/':
                    object_path = ''
            new_path = '/'.join((object_path, child.attrib['name']))
            result.extend( pathNames(bus, service, new_path,paths,blacklist) )
        else:
            if object_path == "":
                object_path = "/"
            functiondict = {}
            
            paths[object_path][child.attrib["name"]] = functiondict
            #for func in child.getchildren():
            for func in list(child):
                if func.tag not in functiondict.keys():
                    functiondict[func.tag] =[]
                functiondict[func.tag].append(func.attrib["name"])
                
                # get current value
                val = dbus_getvalue_ve(bus, service, object_path)                
                
                # some checks and add to result
                if func.attrib["name"] == "GetValue" and not isinstance(val, dbus.Dictionary) and not isinstance(val, dbus.Array) and not any(s in object_path for s in blacklist):
                    result.append(object_path)                     
    
    return result
    

def dbus_getvalue_ve(bus, service, object_path):
    object = bus.get_object(service, object_path)
    return object.GetValue()


# === MAIN ===
bus = dbus.SystemBus()

# step through config services
while(True): 
    try:
        output = ""
        
        # step throug configured services
        for key in _ServicePathConfig.keys():
            output += ("===> %s\n" % key)
            
            
            # check path config for service
            # add dynamic if empty
            # if not take config    
            if not _ServicePathConfig[key] or len(_ServicePathConfig[key]) == 0:
                _ServicePathConfig[key] = pathNames(bus, key, blacklist=_BlacklistPathConfig)
            
            # print paths and current values
            for value in _ServicePathConfig[key]:
                output += ("     - %s: %s\n" % (value,dbus_getvalue_ve(bus, key, value)))
        
        # update output
        os.system('clear||cls')
        print(output) 

        
        time.sleep(_RefreshSleep)
    except Exception as e:
       print(e)
