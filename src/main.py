
import config
import praw
import requests
import os


def processImage(infile):
    try:
        im = Image.open(infile)
    except IOError:
        print "Cant load", infile
        sys.exit(1)
    i = 0
    mypalette = im.getpalette()

    try:
        while 1:
            im.putpalette(mypalette)
            new_im = Image.new("RGBA", im.size)
            new_im.paste(im)
            new_im.save('foo'+str(i)+'.png')

            i += 1
            im.seek(im.tell() + 1)

    except EOFError:
        pass # end of sequence



        
                    
def get_file(url):
    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open("temp_gif", 'wb') as f:
            for chunk in r.iter_content(2048):
                f.write(chunk)

                if os.path.getsize("temp_gif") > 100000000:
                    return False
        return True

    else:
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
            sys.exit()
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
            if not message.was_comment:
                continue
        
        post = message.submission
        if post.is_self:
            continue

        url = post.url
        gif_downloaded = get_file(url)

        if not gif_downloaded:
            os.remove("temp_gif")
            continue

if __name__ == "__main__":
    main()

