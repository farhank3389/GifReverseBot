
import config
import praw
import requests

bot = praw.Reddit(
        user_agent    = "gifreversebot",
        client_id     = config.clientid,
        client_secret = config.secret,
        username      = config.username,
        password      = config.password)


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



