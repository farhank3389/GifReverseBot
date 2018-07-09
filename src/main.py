
import config
import praw

bot = praw.Reddit(
        user_agent    = "gifreversebot",
        client_id     = config.clientid,
        client_secret = config.secret,
        username      = config.username,
        password      = config.password)

