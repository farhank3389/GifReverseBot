import config
import praw
import requests
import os
import subprocess
import time
from urllib.parse import urlparse


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
            for chunk in r.iter_content(2048):
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


def main():
    bot = praw.Reddit(
            user_agent    = "gifreversebot",
            client_id     = config.clientid,
            client_secret = config.secret,
            username      = config.username,
            password      = config.password)

    while True:
        for message in bot.inbox.unread():

            try:
                os.remove('/tmp/temp_gif')
            except FileNotFoundError:
                pass
            try:
                os.remove('/tmp/reverse.mp4')
            except FileNotFoundError:
                pass

            message.markread()

            if not message.was_comment:
                continue
        
            post = message.submission
            if post.is_self:
                continue
            
            url = post.url
            gif_downloaded = get_file(url)

            if not gif_downloaded:
                continue
            
            gif_reversed = process_image("/tmp/temp_gif", "/tmp/reversed.mp4")
            if not gif_reversed:
                continue

        




        
        time.sleep(5)

if __name__ == "__main__":
    main()

