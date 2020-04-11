#bot.py
# -*- coding: utf-8 -*-

import os
import sys
import random
import asyncio
import discord
import wget
import youtube_dl
import requests

from dotenv import load_dotenv
from discord.ext import commands
from delorean import Delorean
from delorean import epoch
from datetime import timedelta


load_dotenv()
TOKEN = os.environ.get('DISCORD_TOKEN')
STATUS = '🦌 | !как'


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

time_var = {}
timer_run = {}
voice = {}
player_queue = {}


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
        'стоп': [' ⏲ Останавливает секундомер и показывает результат', 'Останавливает секундомер\
         и показывает результат'],
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

        await ctx.send('<@' + str(ctx.message.author.id) + '>' + ', перевожу: \n```' + sub_ + ' \
        -> ' + sub_.translate(layout) + '```')
    else:
        await ctx.send('Эта функция переводит текст в русскую раскладку. Текст вводится в кавычках')


async def timer_routine(ctx, timer_var, message, idd):
    await bot.wait_until_ready()

    while not bot.is_closed() and not (timer_run[idd] is False or timer_var <= 0):
        timer_var -= 1
        time_left = timedelta(seconds=timer_var)
        await message.edit(content='Осталось ' + str(time_left))
        await asyncio.sleep(1)

    timer_run.pop(idd)
    await message.delete()
    await ctx.send('<@'+str(ctx.author.id)+'>' + ', таймер завершил отсчет!')

'''
async def player_routine(ctx, guild):
    await bot.wait_until_ready()
    
    while not bot.is_closed() and player_queue[guild]:
        await asyncio.sleep(1)

'''


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


@bot.command(name='голос')
async def join(ctx):
    guild = str(ctx.guild.id)
    global voice

    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
    else:
        return await ctx.send("Сначала вам нужно присоединиться к голосовому каналу!")
    #
    if ctx.voice_client is not None:
        await voice[guild].move_to(channel)
        await ctx.send('Переместился на канал {}'.format(channel))
    else:
        voice[guild] = await channel.connect()
        await ctx.send('Присоединяюсь к каналу {}'.format(channel))


@bot.command(name='цыц')
async def voice_leave(ctx):
    guild = str(ctx.guild.id)
    if voice[guild].is_connected():
        await voice[guild].disconnect()


@bot.command(name='плеер')
async def voice_play(ctx, cmd: str = '', source: str = '', query: str = ''):
    if cmd == 'играй':
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.voice_client is None:
                return await ctx.send('Присоедините меня к голосовому каналу командой `!голос`')
            elif source != '':
                if source == 'ютуб' and query != '':
                    player = await YTDLSource.from_url(query, loop=bot.loop)
                    saved_player = ctx.voice_client.pause()
                    async with ctx.typing():
                        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                    await ctx.send('Играю аудио с YouTube: {}'.format(player.title))
                elif source == 'стрим' and query != '':
                    player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
                    saved_player = ctx.voice_client.pause()
                    async with ctx.typing():
                        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                    await ctx.send('Воспроизвожу стрим с YouTube: {}'.format(player.title))
                else:
                    await ctx.send('Не могу найти источник аудио')
            else:
                await ctx.send('Неверно запрошено воспроизведение')
        else:
            await ctx.send('Присоединитесь к голосовому каналу')
    elif cmd == 'стоп':
        ctx.voice_client.stop()
        await ctx.send('Воспроизведение остановлено')
    elif cmd == 'пауза':
        ctx.voice_client.pause()
        await ctx.send('Воспроизведение приостановлено')
    elif cmd == 'прод':
        ctx.voice_client.resume()
        await ctx.send('Воспроизведение продолжено')
    elif cmd == 'громкость':
        if source != '':
            volume = int(source)
            ctx.voice_client.source.volume = volume / 100
            await ctx.send("Changed volume to {}%".format(volume))
    else:
        await ctx.send('Нет такой команды')
"""
    guild = str(ctx.guild.id)
    query0 = 'G:/GitHub/olenetron/audio/' + query
    if ctx.author.voice and ctx.author.voice.channel:
        if ctx.voice_client is None:
            return await ctx.send('Присоедините меня к голосовому каналу командой `!голос`')
        else:
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query0))
            ctx.voice_client.stop()
            ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

            await ctx.send('Играет: {}'.format(query))
    else:
        await ctx.send('Присоединитесь к голосовому каналу')
"""


@bot.command(name='олень')
async def deer(ctx):
    return await custom_help(ctx, '')


@bot.command(name='пинг')
async def ping(ctx):
    await ctx.send('🏓 Понг! {0} мс'.format(round(bot.latency*1000)))


@bot.command(name='текст')
async def porf_request(ctx, init: str = '', length: int = 30):
    if init == '':
        return await ctx.send('Введите текст запроса в кавычках')

    url = 'https://models.dobro.ai/gpt2/medium/'
    request = {
        'prompt': init,
        'length': length,
        'num_samples': 1
    }
    async with ctx.typing():
        response = requests.post(url, json=request)
        data = response.json()
    await ctx.send(init + str(data['replies'][0]))


@bot.command(name='вслух')
async def porf_request(ctx, init: str = '', length: int = 30):
    if init == '':
        return await ctx.send('Введите текст запроса в кавычках')

    url = 'https://models.dobro.ai/gpt2/medium/'
    request = {
        'prompt': init,
        'length': length,
        'num_samples': 1
    }
    async with ctx.typing():
        response = requests.post(url, json=request)
        data = response.json()
    await ctx.send(init + str(data['replies'][0]), tts=True)


# @bot.command(name='create-channel')
# @commands.has_role('admin')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Недостаточно полномочий.')

bot.run(TOKEN)
