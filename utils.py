import os
import requests
import shutil

def download_file(url, folder_name):
    local_filename = url.split('/')[-1]
    path = os.path.join("/{}/{}".format(folder_name, local_filename))
    with requests.get(url, stream=True) as r:
        with open(path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename

def get_nick(obj):
    if hasattr(obj, "nick") and obj.nick is not None:
        return obj.nick
    else:
        return obj.name