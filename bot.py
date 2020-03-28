#bot.py

import os
import random

from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()
TOKEN = os.environ.get('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')


@bot.command(name='олень', help='Только попробуй назвать его оленем!')
async def nine_nine(ctx):
    response = 'Сам олень!'
    await ctx.send(response)


@bot.command(name='кости' or 'roll', help='Кинуть кости (!кости <кол-во костей> <кол-во сторон> ')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))


# @bot.command(name='create-channel')
# @commands.has_role('admin')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Недостаточно полномочий.')

bot.run(TOKEN)
