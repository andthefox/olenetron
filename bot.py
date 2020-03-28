#bot.py

import os
import random

from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()
TOKEN = os.environ.get('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')


@bot.command(name='99')
async def nine_nine(ctx):
    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]
    response = random.choice(brooklyn_99_quotes)
    await ctx.send(response)


@bot.command(name='олень')
async def nine_nine(ctx):
    response = 'Сам олень!'
    await ctx.send(response)

bot.run(TOKEN)
