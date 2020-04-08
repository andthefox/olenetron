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
timer_run = {}

async def custom_help(ctx, command=''):
    embed = discord.Embed(
        colour=discord.Colour.green()
    )

    coms = {
        'как': [' 🦌 Выводит доступные команды или подробную информацию о команде', 'Выводит доступные команды или \
        подробную информацию о команде'],
        'кинь': [' 🎲 Кидает кубики', 'Кинуть кубики *x* сторон *y* раз'],
        'переведи': [' 🔄 Перевод раскладки текста', 'Переводит текст в нужную раскладку'],
        'старт': [' ⏲ Запускает секундомер', 'Запускает секундомер'],
        'стоп': [' ⏲ Останавливает секундомер и показывает результат', 'Останавливает секундомер и показывает результат'],
        'таймер': [' ⏳ Запускает таймер', 'таймер `старт <число> <сек|мин|час>`, `стоп`'],
        'пинг': ['🏓 Задержка бота', 'Время задержки ответа бота в миллисекундах']
    }

    if command == '':
        embed.set_author(name='Команды бота 🛠')
        for key in coms:
            value = coms[key]
            embed.add_field(name='!'+key, value=value[0], inline=False)
        embed.add_field(name='---', value='Кстати, боту можно писать и напрямую 😎', inline=False)
    else:
        embed.set_author(name='Поиск по команде 🔎')
        if command in coms:
            embed.add_field(name='!' + command, value=coms[command][1], inline=False)
        else:
            embed.add_field(name='!' + command, value='Нет такой команды 🤷‍♂️', inline=False)

    await ctx.send('', embed=embed)


async def translate(ctx, sub_: str):
    symbols_en = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"\
                 'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~&'

    symbols_ru = "йцукенгшщзхъфывапролджэячсмитьбю.ё"\
                 'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё?'
    en = 0
    ru = 0

    if sub_:
        for k in range(len(sub_)):
            if sub_[k] in symbols_en:
                en += 1
            if sub_[k] in symbols_ru:
                ru += 1

        if en > ru:
            layout = dict(zip(map(ord, symbols_en), symbols_ru))
        else:
            layout = dict(zip(map(ord, symbols_ru), symbols_en))

        await ctx.send('<@' + str(ctx.message.author.id) + '>' + ', перевожу: \n```' + sub_ + ' -> ' + sub_.translate(layout) + '```')
    else:
        await ctx.send('Эта функция переводит текст в русскую раскладку. Текст вводится в кавычках')


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=STATUS))
    print(bot.user.name + ' is ready.')


@bot.command(name='как')
async def run_help(ctx, command=''):
    await custom_help(ctx, command)


@bot.command(name='переведи')
async def run_translate(ctx, sub_: str = ''):
    await translate(ctx, sub_)


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
async def start_counter(ctx):
    dt = Delorean()
    name = ctx.author.name
    if ctx.guild:
        guild = str(ctx.guild.id)
    else:
        guild = 'noguild'

    ident = str(name+'@'+guild)

    out = [', поехали! 💨', ', часики уже тикают! ⏲']

    if ident in time_var:
        response = name + out[1]
    else:
        time_var[ident] = dt.epoch
        response = name + out[0]

    await ctx.send(response)


@bot.command(name='стоп')
async def stop_counter(ctx):
    dte = Delorean()
    name = ctx.author.name
    if ctx.guild:
        guild = str(ctx.guild.id)
    else:
        guild = 'noguild'
    ident = str(name + '@' + guild)

    if ident in time_var:
        dts = time_var.pop(ident)
        r = dte.epoch - dts
        rr = epoch(r)
        response = name + ', твоё время: ' + rr.datetime.strftime("%H:%M:%S") + ' 🏁'
    else:
        response = 'Старта не было 😒'

    await ctx.send(response)


@bot.command(name='таймер')
async def timer_handler(ctx, funx: str = '', val: int = 5, dfn: str = 'мин'):
    name = ctx.author.name
    if ctx.guild:
        guild = str(ctx.guild.id)
    else:
        guild = 'noguild'
    ident = str(name + '@' + guild)

    async def timer_start():
        dfn_transpose = {
            'мин': 60,
            'сек': 1,
            'час': 3600
        }

        if val and dfn:
            value = val * dfn_transpose[dfn]
        else:
            value = 0

        if 0 < value <= 7200:
            if ident not in timer_run:
                response = '⏳ таймер запущен на ' + str(val) + ' ' + dfn + '. (' + str(value) + ' секунд)'
                await ctx.send(response)
                msg = await ctx.send('Осталось ...')
                bot.loop.create_task(timer_routine(ctx, value, msg, ident))
                timer_run[ident] = True
                # https://stackoverflow.com/questions/45824314/break-loop-with-command
            else:
                await ctx.send(content='⏳ таймер уже запущен')
        else:
            await ctx.send(content='🤔 кажется, указано неверное время!')

    async def timer_stop():
        if ident in timer_run:
            timer_run[ident] = False
        else:
            await ctx.send(content='Нечего останавливать 🤷‍♀️')

    async def do_default():
        response = 'таймер `старт <число> <сек|мин|час>`'
        await ctx.send(response)

    action = {
        '': do_default,
        'старт': timer_start,
        'стоп': timer_stop
    }

    return await action[funx]()


async def timer_routine(ctx, timer_var, message, idd):
    await bot.wait_until_ready()

    while not bot.is_closed() and not (timer_run[idd] is False or timer_var <= 0):
        timer_var -= 1
        await message.edit(content='Осталось ' + str(timer_var))
        await asyncio.sleep(1)

    timer_run.pop(idd)
    await message.delete()
    await ctx.send('<@'+str(ctx.author.id)+'>' + ', таймер завершил отсчет!')


@bot.command(name='олень')
async def deer(ctx):
    return await custom_help(ctx, '')


@bot.command(name='пинг')
async def ping(ctx):
    await ctx.send('🏓 Понг! {0} мс'.format(round(bot.latency*1000)))

# @bot.command(name='create-channel')
# @commands.has_role('admin')


# @bot.loop()
# async def my_background_task(self):


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Недостаточно полномочий.')

bot.run(TOKEN)
