# Stonks
A Discord bot to manage your stocks in Codeforces! On registering your Codeforces handle with the bot, the bot gives you 100 of your stocks and $20 of cash. You can sell your stocks, or buy other stocks from the market. The price of the stocks depend on your rating, and is given by the formula `(1.2)^rank * rating/100` where rank is the number of ranks above Newbie.

## How to setup?

- Create a Discord bot and get it's token. Follow the instructions [here](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token)!

- Then export the token as an environment variable:
```
export STONKS_TOKEN="<YOUR TOKEN>"
```

- Install the latest version of discord.py using `pip install -U discord.py`.

- Run the bot using `python main.py` (requires Python 3.7 or above)!

- The prefix is `+`. To get started, register your Codeforces handle first using the `+register` command. Type `+help` for a list of commands.

- Note that the Admin-only commands require you to have a role called "Admin".

## Screenshots

![](https://github.com/iammanish17/Stonks/blob/master/screenshots/screen1.png)
![](https://github.com/iammanish17/Stonks/blob/master/screenshots/screen2.png)
![](https://github.com/iammanish17/Stonks/blob/master/screenshots/screen3.png)
