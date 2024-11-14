#%%
import requests

file='C:/Users/e_par/Downloads/slot/May 30 2023, 5.13 PM.slot'

data = {
    "file": open(file, "rb"),
    #"maxDownloads": 100,
    #"autoDelete": True
}



#%%
url = 'https://polyutils.dumbserg.al/ace/mode-json.js'
response = requests.get(url, files=data)
res = response.json()
print(res)
print(res["link"])
# %%
