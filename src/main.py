import config
import praw
import requests
import os
import subprocess
import time
from urllib.parse import urlparse


REPLY = """[Here is a reversed version of the gif](https://gfycat.com/{})


&nbsp;

---

This action was performed by a bot. I am still being developed so I will probably make mistakes :(. Send me a PM if you find an issue."""

def process_file(infile, outfile):
    with open('/dev/null', 'a') as null:
        ret = subprocess.run(['/usr/bin/ffmpeg', '-i', infile, '-vf', 'reverse', outfile], shell=False, stdout=null, stderr=null)

    try:
        ret.check_returncode()
    except subprocess.CalledProcessError as e:
        # log error
        return False
    
    return True
                    
def get_file(url):

    parse = urlparse(url)
    if parse.path.endswith('.gifv'):
        replace_gifv = parse._replace(path = parse.path[:-4] + 'mp4')
        url = replace_gifv.geturl()

    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open("/tmp/temp_gif", 'wb') as f:
            for chunk in req.iter_content(2048):
                f.write(chunk)

                if os.path.getsize("/tmp/temp_gif") > 100000000:
                    return False
        return True

    else:
        # log
        return False


def get_token(client_id, client_secret):
        payload = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
                }
        req = requests.post('https://api.gfycat.com/v1/oauth/token', data=str(payload))
        res = req.json()
        if not 'access_token' in res:
            print ('ERROR: Gfycat API is not available. Please try again later.')
            sys.exit() # need to change this
        return res['access_token']

def upload_file(outFile, accessToken, title):
    headers = { 'Authorization': 'Bearer {}'.format(accessToken) }
    data = '{{"title":{}}}'.format(title)

    gfycat_name = requests.post("https://api.gfycat.com/v1/gfycats", data = data, headers = headers)
    
    for i in range(2): # try twice again if it fails
        if gfycat_name.status_code == 401:
            accessToken = get_token(config.gfycatID, config.gfycatSecret)
            headers = { "Authorization": "Bearer {}".format(accessToken) }
            gfycat_name = requests.post("https://api.gfycat.com/v1/gfycats", data = data, headers = headers)
        else:
            break

    if gfycat_name.status_code == 401:
        return

    gfyname = gfycat_name.json()["gfyname"]
    
    with open(outFile, 'rb') as f:
        send_file = requests.put("https://filedrop.gfycat.com/" + gfyname, data=f)
        print(send_file.status_code)
        if send_file.status_code != 200:
            return
        return gfyname

def check_status(gfyname):
    req = requests.get("https://api.gfycat.com/v1/gfycats/fetch/status/" + gfyname)
    if req.status_code != 200:
        time.sleep(5)
        return False

    status = {"task":"encoding"}
    count = 0
    while status["task"] == "encoding":
        req = requests.get("https://api.gfycat.com/v1/gfycats/fetch/status/" + gfyname)
        if req.status_code != 200:
            time.sleep(5)
            return

        status = req.json().get("task")
        if status is None:
            return
        if status == "complete":
            return "https://api.gfycat.com/v1/gfycats/fetch/status/" + gfyname 
        
        time.sleep(3)
        count += 1
        if count > 50:
            return

def delete_files():
    try:
        os.remove('/tmp/temp_gif')
    except FileNotFoundError:
        pass
    try:
        os.remove('/tmp/reversed.mp4')
    except FileNotFoundError:
        pass

def main():
    bot = praw.Reddit(
            user_agent    = "gifreversebot",
            client_id     = config.clientid,
            client_secret = config.secret,
            username      = config.username,
            password      = config.password)

    while True:
        for message in bot.inbox.unread():
            print('received message: ' + repr(message.body))

            delete_files()

            message.mark_read()

            if not message.was_comment or message.body != "/u/redditgifreversebot":
                print("continuing")
                continue
        
            post = message.submission
            if post.is_self:
                continue
            
            url = post.url
            gif_downloaded = get_file(url)
            if not gif_downloaded:
                continue
            
            gif_reversed = process_file("/tmp/temp_gif", "/tmp/reversed.mp4")
            if not gif_reversed:
                continue

            gfycatToken = get_token(config.gfycatID, config.gfycatSecret)

            title = post.shortlink
            if len(title) > 131:
                title = title[:-(9 - (140 % len(title)))]
            title = title + " Reversed"

            gfyname = upload_file("/tmp/reversed.mp4", gfycatToken, title)
            if gfyname is None:
                continue
            status = check_status(gfyname)
            if gfyname is None:
                continue

            message.reply(REPLY.format(gfyname))

        time.sleep(5)

if __name__ == "__main__":
    main()

