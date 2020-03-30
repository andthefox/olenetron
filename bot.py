#bot.py
# -*- coding: utf-8 -*-

import os
import random
import asyncio
import discord
import wget

from dotenv import load_dotenv
from discord.ext import commands
from delorean import Delorean
from delorean import epoch

load_dotenv()
TOKEN = os.environ.get('DISCORD_TOKEN')
STATUS = '🦌 | !как'

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

time_var = {}


async def custom_help(ctx, command=''):
    embed = discord.Embed(
        colour=discord.Colour.green()
    )

    coms = {
        'как': [' 🦌 Выводит доступные команды или подробную информацию о команде', 'Выводит доступные команды или \
        подробную информацию о команде'],
        'кинь': [' 🎲 Кидает кубики', 'Кинуть кубики *x* сторон *y* раз'],
        'старт': [' ⏲ Запускает секундомер', 'Запускает секундомер'],
        'стоп': [' ⏲ Останавливает секундомер и показывает результат', 'Останавливает секундомер и показывает результат'],
    }

    if command == '':
        embed.set_author(name='Команды бота 🛠')
        for key in coms:
            value = coms[key]
            embed.add_field(name='!'+key, value=value[0], inline=False)
        embed.add_field(name='---', value='Кстати, боту можно писать и напрямую 😎', inline=False)
    elif command == 'какоть' or command == 'какать':
        kak_kakat = '🧻 **Я ВАМ ЗАПРЕЩАЮ** \n\t`срать`*!*'
        return await ctx.send(kak_kakat)
    else:
        embed.set_author(name='Поиск по команде 🔎')
        if command in coms:
            embed.add_field(name='!' + command, value=coms[command][1], inline=False)
        else:
            embed.add_field(name='!' + command, value='Нет такой команды 🤷‍♂️', inline=False)

    await ctx.send('', embed=embed)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=STATUS))
    print(bot.user.name + ' is ready.')


@bot.command(name='как')
async def run_help(ctx, command=''):
    await custom_help(ctx, command)


@bot.command(name='кинь')
async def roll(ctx, number_of_sides: int = 20, number_of_dice: int = 1):
    if 1 < number_of_sides <= 100 and 0 < number_of_dice <= 50:
        dice = [
            '**' + str(random.choice(range(1, number_of_sides + 1))) + '**'
            for _ in range(number_of_dice)
        ]
        name = ctx.message.author.name
        await ctx.send(name + ' кидает кубики ({0}x{1}) 🎲🎲 \nВыпало:\
         \n'.format(number_of_dice, number_of_sides) + ', '.join(dice))
    else:
        await ctx.send('Не кину 😕')


@bot.command(name='старт')
async def start(ctx):
    dt = Delorean()
    name = ctx.message.author.name

    if name in time_var:
        response = name + ', часики уже тикают! ⏲'
    else:
        time_var[name] = dt.epoch
        response = name + ', поехали! 💨'
    await ctx.send(response)


@bot.command(name='олень')
async def deer(ctx, sub: str = '', sub_: str = ''):
    if sub == 'деградни':
        if sub_ == '' or sub_ == 'средне':
            text = 'ыыыыыыыыыы'
        elif sub_ == 'легонько':
            text = 'ыыы'
        elif sub_ == 'сильно':
            text = 'Я роняю запад, У!'
        elif sub_ == 'максимально':
            text = 'Тёмная тема Вконтакте топ'
        await ctx.send(text)
    else:
        await custom_help(ctx, sub_)


@bot.command(name='стоп')
async def stop(ctx):
    dte = Delorean()
    name = ctx.message.author.name

    if name in time_var:
        dts = time_var.pop(name)
        r = dte.epoch - dts
        rr = epoch(r)
        response = name + ', твоё время: ' + rr.datetime.strftime("%H:%M:%S") + ' 🏁'
    else:
        response = 'Старта не было 😒'

    await ctx.send(response)

# @bot.command(name='create-channel')
# @commands.has_role('admin')


# @bot.loop()
# async def my_background_task(self):


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Недостаточно полномочий.')

bot.run(TOKEN)
