#bot.py

import os
import random
import discord
import wget

from dotenv import load_dotenv
from discord.ext import commands
from delorean import Delorean
from delorean import epoch

load_dotenv()
TOKEN = os.environ.get('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

time_var = {}


@bot.event
async def on_ready():
    print('Bot is ready.')


@bot.command(name='хелп')
async def custom_help(ctx, command=''):
    embed = discord.Embed(
        colour=discord.Colour.green()
    )

    coms = {
        'хелп': 'Выводит доступные команды',
        'олень': 'Только попробуй назвать его оленем!',
        'кинь': '!кинь <кол-во сторон> [кол-во костей]'
    }

    if command == '':
        for key in coms:
            value = coms[key]
            embed.add_field(name='!'+key, value=value, inline=False)
    else:
        if command in coms:
            embed.add_field(name='!' + command, value=coms[command], inline=False)
        else:
            embed.add_field(name='!' + command, value='Нет такой команды :(', inline=False)

    await ctx.send('Команды бота:', embed=embed)


@bot.command(name='олень')
async def deer(ctx):
    response = 'Сам олень!'
    await ctx.send(response)


@bot.command(name='кинь')
async def roll(ctx, number_of_sides: int = 20, number_of_dice: int = 1):
    if 1 < number_of_sides <= 100 and 0 < number_of_dice <= 50:
        dice = [
            '**' + str(random.choice(range(1, number_of_sides + 1))) + '**'
            for _ in range(number_of_dice)
        ]
        await ctx.send('Выпало {0} кубов по {1}: \n'.format(number_of_dice, number_of_sides) + ', '.join(dice))
    else:
        await ctx.send('Не кину :(')


@bot.command(name='время')
async def deer(ctx):
    dt = Delorean()
    await ctx.send(dt.datetime.strftime("%d.%m.%Y %H:%m:%S"))


@bot.command(name='старт')
async def deer(ctx):
    dt = Delorean()
    name = ctx.message.author.name
    time_var[name] = dt.epoch
    response = str(name) + ', поехали!'
    await ctx.send(response)


@bot.command(name='стоп')
async def deer(ctx):
    dte = Delorean()
    name = ctx.message.author.name

    if name in time_var:
        dts = time_var.pop(name)
        r = dte.epoch - dts
        rr = epoch(r)
        response = str(name) + ', твоё время: ' + rr.datetime.strftime("%H:%M:%S")
    else:
        response = 'Старта не было :)'

    await ctx.send(response)

# @bot.command(name='create-channel')
# @commands.has_role('admin')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Недостаточно полномочий.')

bot.run(TOKEN)
