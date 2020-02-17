import logging
from discord.ext import commands
from discord.ext.commands import Bot
from os import environ
from discord import Game


def isprivate(ctx):
    return ctx.guild is not None


logging.basicConfig(level=logging.INFO)
description = '''Stonks'''
client = Bot(description="A Discord bot to manage your stocks in Codeforces", command_prefix="+")
client.add_check(isprivate)


@client.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send_help(ctx.command)
    else:
        logging.info(str(error))


@client.event
async def on_ready():
    await client.change_presence(activity=Game(name="with stocks"))
    logging.info('Logged in as')
    logging.info(client.user.name)
    logging.info(client.user.id)
    logging.info('------')

if __name__ == "__main__":
    client.load_extension("stocks")

token = environ.get('STONKS_TOKEN')
if not token:
    logging.error('Bot token not found!')
else:
    client.run(token)
