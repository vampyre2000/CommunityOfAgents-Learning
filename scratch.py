from datetime import date
from datetime import datetime
import os
import platform
#datetime.now().strftime('%A')
'Wednesday'
today = date.today()
print("Today's date:", today)
print(datetime.now().strftime('%A'))

def get_evironment_details():
        print(platform.system())
        print(platform.machine())
        print(platform.release())
        print(platform.version())
        print(platform.processor())
        print(platform.python_version())
        print(platform.uname())
    
def get_like_distro():
    info = platform.freedesktop_os_release()
    ids = [info["ID"]]
    if "ID_LIKE" in info:
        # ids are space separated and ordered by precedence
        ids.extend(info["ID_LIKE"].split())
    #return ids
    print(ids)

get_evironment_details()

get_like_distro()
