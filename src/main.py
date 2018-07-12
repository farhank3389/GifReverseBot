import config
import praw
import requests
import os
import subprocess
import time
import logging
from urllib.parse import urlparse


REPLY = """[Here is a reversed version of the gif](https://gfycat.com/{})


&nbsp;

---

This action was performed by a bot. I am new and still being developed so I will probably make mistakes :(.  Please send me a PM if you find an issue."""

def process_file(infile, outfile):
    logger.debug("Processing {} to {}".format(infile, outfile))
    with open('/tmp/ffmpeg_log.log', 'w') as log:
        ret = subprocess.run(['/usr/bin/ffmpeg', '-threads', '3', '-i', infile, '-vf', 'reverse', outfile], shell=False, stdout=log, stderr=log)

    try:
        ret.check_returncode()
    except subprocess.CalledProcessError as e:
        # log error
        return False
    
    return True
                    
def get_file(url):

    parse = urlparse(url)

    if parse.netloc.lower() == "gfycat.com":
        gfyname = parse.path.strip("/")
        url = requests.get("https://api.gfycat.com/v1/gfycats/" + gfyname)
        if url.status_code  != 200:
            return
        
        json = url.json()

        if "errorMessage" in json:
            return

        url = json["gfyItem"]["mp4Url"]

    elif parse.netloc.lower() == "i.imgur.com":
        if parse.path.endswith('.gifv'):
            replace_gifv = parse._replace(path = parse.path[:-4] + 'mp4')
            url = replace_gifv.geturl()
    elif parse.netloc.lower() not in ("giant.gfycat.com", "zippy.gfycat.com", "i.redd.it"):
        print("Not imgur or gfycat link")
        return

    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open("/tmp/temp_gif", 'wb') as f:
            for chunk in req.iter_content(2048):
                f.write(chunk)

                if os.path.getsize("/tmp/temp_gif") > 20000000:
                    return
        return True

    else:
        # log
        return


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
    print(gfyname)
    
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

    status = "encoding"
    print(status, type(status))
    count = 0
    while status == "encoding":
        req = requests.get("https://api.gfycat.com/v1/gfycats/fetch/status/" + gfyname)
        if req.status_code != 200:
            time.sleep(1)
            return
        req= req.json()

        status = req.get("task")
        if status is None:
            return
        if status == "complete":
            if "gfyname" in req:
                return req["gfyname"]
            return gfyname 
        
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

            if not message.was_comment or message.body.lower() != "/u/redditgifreversebot":
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
                print("upload file returned None")
                continue
            gfyname = check_status(gfyname)
            if gfyname is None:
                print("check status returned None")
                continue
            
            print("replying with: " + REPLY.format(gfyname))
            err = "RATELIMIT"
            while "RATELIMIT" in err:
                try:
                    message.reply(REPLY.format(gfyname))
                    err = ""
                except praw.exceptions.APIException as e:
                    err = str(e)
                    print(err)
                    print(0)
                    sleep = err.split("RATELIMIT: 'you are doing that too much. try again in ")[1].split(".' on field 'ratelimit'")[0].split()
                    print(sleep)
                    if sleep[1] ==  "minutes":
                        sleep = int(sleep[0]) * 60
                    else:
                        sleep = int(sleep[0])
                    print(err)
                    print("sleeping for {} seconds".format(sleep))
                    time.sleep(sleep + 15)


        time.sleep(5)

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.setLevel(config.logLevel)

    handler = logging.FileHandler(config.logFile)
    handler.setLevel(config.logLevel)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.info("Starting...")
    main()

