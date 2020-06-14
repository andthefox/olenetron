# bot.py
# -*- coding: utf-8 -*-

import os
import io
import sys
import random
import asyncio
import discord
import wget
import youtube_dl
import requests
import boto3
from PIL import Image
import json
import html
import feedparser

from dotenv import load_dotenv
from discord.ext import commands
from delorean import Delorean
from delorean import epoch
from datetime import timedelta

load_dotenv()
TOKEN = os.environ.get('DISCORD_TOKEN')
STATUS = '🦌 | !как'

s3 = boto3.resource('s3')
bucket = s3.Bucket(os.environ.get('S3_BUCKET_NAME'))
jsondata = {}

for key in bucket.objects.all():
    print(key)

json_object = bucket.Object('data.json')


def prepare_json_data():
    global json_object
    json_object.download_file('data.json')
    global jsondata
    with open('data.json') as json_file:
        jsondata = json.load(json_file)
    print(json.dumps(jsondata, indent=4))


def modify_json_data():
    global jsondata
    # print(json.dumps(jsondata, indent=4))
    with open('data.json', 'w') as output:
        json.dump(jsondata, output)


def upload_json_data():
    global json_object
    json_object.upload_file('data.json')


def synthesize(text, ssml=False, apikey=os.environ.get('YANDEX_API_KEY'), emotion='good', voice='omazh'):
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Api-Key ' + apikey,
    }

    data = {
        'lang': 'ru-RU',
        'emotion': emotion,
        'voice': voice
    }
    if ssml is True:
        data['ssml'] = text
    else:
        data['text'] = text

    with requests.post(url, headers=headers, data=data, stream=True) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        for chunk in resp.iter_content(chunk_size=None):
            yield chunk


prepare_json_data()

# putting objects
'''
data = open('693845376024707123.mp3', 'rb')
bucket.put_object(Key='693845376024707123.mp3', Body=data)
'''

# loading images
'''
my_object = bucket.Object('693845376024707123.jpg')
stream = io.BytesIO(my_object.get()['Body'].read())
img = Image.open(stream)
img.show()
'''

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
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
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

    @classmethod
    async def get_title(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        return data.get('title')


bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

time_var = {}
timer_run = {}
voice = {}


async def custom_help(ctx, command=''):
    embed = discord.Embed(
        colour=discord.Colour.green()
    )

    coms = {
        'как/олень': [' 🦌 Выводит доступные команды или подробную информацию о команде', 'Выводит доступные \
команды или подробную информацию о команде'],
        'кинь': [' 🎲 Кидает кубики', 'Кинуть кубики *x* сторон *y* раз'],
        'переведи': [' 🔄 Перевод раскладки текста', 'Переводит текст в нужную раскладку'],
        'старт': [' ⏲ Запускает секундомер', 'Запускает секундомер'],
        'стоп': [' ⏲ Останавливает секундомер и показывает результат', 'Останавливает секундомер \
и показывает результат'],
        'таймер': [' ⏳ Запускает таймер', 'таймер `старт <число> <сек|мин|час>`, `стоп`'],
        'пинг': [' 🏓 Задержка бота', 'Время задержки ответа бота в миллисекундах'],
        'голос': [' 🔊 Добавляет бота в Ваш голосовой канал', 'Добавляет бота в Ваш голосовой канал'],
        'цыц': [' 🔈 Бот покидает голосовой канал', 'Бот покидает голосовой канал'],
        'плеер': [' ▶ воспроизведение аудио. Подробно: `!как плеер`', 'Использование: !плеер \n\
`ютуб|стрим [ссылка/"поиск"]`, `файл [*.mp3/*.mp4]`,  `стоп`, `пауза`, `прод`, `громкость [процент]`'],
        'текст': [' 💬 Генератор теста из слова, фразы или предложения на базе https://porfirevich.ru/', '!\
текст [слова] <число слов на выходе>'],
        'дрим': [' 🖼 Обработать изображение с помощью deepdream', '\
Прикрепите к сообщению с командой изображение или ссылку']
    }

    if command == '':
        embed.set_author(name='Команды бота 🛠')
        for k in coms:
            value = coms[k]
            embed.add_field(name='!'+k, value=value[0], inline=False)
        embed.add_field(name='---', value='Кстати, боту можно писать и напрямую 😎', inline=False)
    else:
        embed.set_author(name='Поиск по команде 🔎')
        if command in coms:
            embed.add_field(name='!' + command, value=coms[command][1], inline=False)
        else:
            embed.add_field(name='!' + command, value='Нет такой команды 🤷‍♂️', inline=False)

    await ctx.send('', embed=embed)


async def timer_routine(ctx, v, message, idd):
    await bot.wait_until_ready()
    while not bot.is_closed() and not timer_run[idd] is False:
        dt = Delorean()
        now = dt.epoch
        delta = v-now
        if delta <= 0:
            break
        time_left = timedelta(seconds=delta)
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
async def run_translate(ctx, *, sub_):
    symbols_en = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`" \
                 'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~&'

    symbols_ru = "йцукенгшщзхъфывапролджэячсмитьбю.ё" \
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
                dt = Delorean()
                response = '⏳ таймер запущен на ' + str(val) + ' ' + dfn + '. (' + str(value) + ' секунд)'
                await ctx.send(response)
                msg = await ctx.send('Осталось ...')
                value = dt.epoch + value
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


async def add_to_queue(ctx, play_type, data):
    global jsondata
    init_loop = False
    # {server:id {user:name; type(youtube, file, text); data} }into json file
    guild = str(ctx.guild.id)

    if guild not in jsondata:
        jsondata[guild] = {}

    if 'queue' in jsondata[guild]:
        voice_queue = jsondata[guild]['queue']
    else:
        voice_queue = []

    if len(voice_queue) == 0:
        init_loop = True

    title = await YTDLSource.get_title(data, loop=bot.loop)

    voice_queue.append({
        'user': ctx.author.name,
        'type': play_type,
        'source': data,
        'title': title
    })

    jsondata[guild]['queue'] = voice_queue
    # print(jsondata)

    modify_json_data()

    if init_loop is True:
        bot.loop.create_task(queue_routine(ctx))
    # upload_json_data()


async def queue_routine(ctx):
    await bot.wait_until_ready()
    guild = str(ctx.guild.id)
    global jsondata

    def move_queue():
        if jsondata[guild]['queue']:
            del jsondata[guild]['queue'][0]

    while not bot.is_closed() and jsondata[guild].get('queue'):
        if ctx.voice_client.is_playing() is False and ctx.voice_client.is_paused() is False:
            source = jsondata[guild]['queue'][0]['source']

            if jsondata[guild]['queue'][0]['type'] == 'yt':
                player = await YTDLSource.from_url(source, loop=bot.loop)
                ctx.voice_client.pause()
                async with ctx.typing():
                    ctx.voice_client.play(player, after=lambda e: print('Player \
error: %s' % e) if e else move_queue())
                await ctx.send('Играю аудио с YouTube: {}'.format(player.title))

            elif jsondata[guild]['queue'][0]['type'] == 'stream':
                player = await YTDLSource.from_url(source, loop=bot.loop, stream=True)
                ctx.voice_client.pause()
                async with ctx.typing():
                    ctx.voice_client.play(player, after=lambda e: print('Player \
error: %s' % e) if e else move_queue())
                await ctx.send('Воспроизвожу стрим с YouTube: {}'.format(player.title))

            if len(jsondata[guild]['queue']) == 1:
                await ctx.send('Это последний трек в очереди. Может, добавим ещё пару? 😉')
            modify_json_data()
        await asyncio.sleep(1)

    if not ctx.voice_client.is_playing() or ctx.voice_client.is_playing() is False and ctx.voice_client.is_paused() is False:
        await ctx.send('Воспроизведение окончено')


@bot.command(name='плеер')
async def voice_play(ctx, cmd: str = '', *, source: str = ''):
    global jsondata
    if cmd == 'ютуб' or cmd == 'стрим' or cmd == 'файл':
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.voice_client is None:
                return await ctx.send('Присоедините меня к голосовому каналу командой `!голос`')
            if cmd == 'ютуб' and source != '':
                await add_to_queue(ctx, 'yt', source)
                await ctx.send('Видео добавлено')
            elif cmd == 'стрим' and source != '':
                await add_to_queue(ctx, 'stream', source)
                await ctx.send('Потоковое воспроизведение добавлено')
                '''    
            elif cmd == 'файл':
                fn = None
                if ctx.message.attachments:
                    fn = ctx.message.attachments[0].filename[-4::]
                if fn and (fn == '.mp3' or fn == '.mp4'):
                    guild = str(ctx.guild.id)
                    await ctx.message.attachments[0].save(str(guild) + fn)
                    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(str(guild) + fn))
                    ctx.voice_client.stop()
                    ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
                    await ctx.send('Играет пользовательский файл')
                else:
                    await ctx.send('Отправьте файл в формате .mp3 или mp4')
                 '''
            else:
                await ctx.send('Невозможно воспроизвести. Проверьте команду')
        else:
            await ctx.send('Присоединитесь к голосовому каналу')

    elif cmd == 'стоп':
        jsondata[str(ctx.guild.id)]['queue'] = []
        modify_json_data()
        ctx.voice_client.stop()
    elif cmd == 'пауза':
        ctx.voice_client.pause()
        await ctx.send('Воспроизведение приостановлено')
    elif cmd == 'вперед' or cmd == 'вперёд' or cmd == 'след':
        ctx.voice_client.stop()
        # bot.loop.create_task(queue_routine(ctx))
    elif cmd == 'прод':
        ctx.voice_client.resume()
        await ctx.send('Воспроизведение продолжено')
    elif cmd == 'громкость':
        if source != '':
            volume = int(source)
            ctx.voice_client.source.volume = float(volume / 100)
            await ctx.send("Changed volume to {}%".format(volume))
    elif cmd == 'очередь':
        out_str = ''
        if len(jsondata[str(ctx.guild.id)]['queue']) != 0:
            i = 0
            for k in jsondata[str(ctx.guild.id)]['queue']:
                out_str += (str(i+1) + ': ' + k['title'] + ' | Добавил @'+k['user'] + '\n')
                i += 1
        else:
            out_str = 'Очередь пуста'
        await ctx.send(out_str)
    else:
        await ctx.send('Нет такой команды')


@bot.command(name='олень')
async def deer(ctx):
    return await custom_help(ctx, '')


@bot.command(name='пинг')
async def ping(ctx):
    await ctx.send('🏓 Понг! {0} мс'.format(round(bot.latency*1000)))


@bot.command(name='текст')
async def porf_request(ctx, *, init: str):
    if not init:
        return await ctx.send('Введите текст запроса в кавычках')

    url = 'https://models.dobro.ai/gpt2/medium/'
    request = {
        'prompt': init,
        'length': 60,
        'num_samples': 1
    }
    async with ctx.typing():
        response = requests.post(url, json=request)
        data = response.json()
    await ctx.send(init + str(data['replies'][0]))


# dream --- make post request with url to another machine
@bot.command(name='дрим')
async def dream(ctx, url: str = None):
    if url is not None:
        img = url
    elif ctx.message.attachments:
        img = ctx.message.attachments[0].url
    else:
        return await ctx.send('Прикрепите изображение или отправьте ссылку вместе с командой')

    async with ctx.typing():
        r = requests.post(
            "https://api.deepai.org/api/deepdream",
            data={
                'image': img,
            },
            headers={'api-key': '8c01fe27-dd5d-40d4-8a09-958e71ae438c'}
        )
        data = r.json()

    if 'output_url' in data:
        await ctx.send('Изображение обработано:\n ' + data['output_url'])
    else:
        await ctx.send('Ошибка:\n ' + data['status'])


@bot.command(name='игра')
async def game(ctx, cmd: str = None):
    global jsondata
    name = ctx.author.name
    if ctx.guild:
        guild = str(ctx.guild.id)
    else:
        guild = 'noguild'
    ident = str(name + '@' + guild)

    initial_values = {
        'money': 10,
        'hp': 100,
        'xp': 1
    }

    if cmd is None:
        '''
            Идеи: ачивки, прозвища, рандом оружие и шмот, статы, баффы, прогрессбар, квесты, расширенный опыт в голосе
        '''
        return await ctx.send('Игра в разработке')
    if cmd == 'старт':
        if 'users' not in jsondata:
            jsondata['users'] = {}
        if ident in jsondata['users']:
            return await ctx.send('Вы уже в игре! 🐉')
        jsondata['users'][ident] = initial_values
        modify_json_data()
        upload_json_data()
        return await ctx.send('Добро пожаловать в игру! 🧙‍♂️')


async def voice_synthesis(text: str, filename):
    with open(filename, "wb") as f:
        # omazh, filipp
        for audio_content in synthesize(text=text, voice='filipp', emotion='neutral'):
            f.write(audio_content)
    return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename))


# @bot.command(name='create-channel')
# @commands.has_role('admin')


@bot.command(name='новости')
async def read_news(ctx, *, index: str = 'главное'):
    if ctx.voice_client is None:
        return await ctx.send('Присоедините меня к голосовому каналу')
    feed = feedparser.parse("https://news.yandex.ru/index.rss")  # главное

    if index == '' or index == 'главное':
        feed = feedparser.parse("https://news.yandex.ru/index.rss")  # главное
    elif index == 'Москва' or index == 'москва':
        feed = feedparser.parse("https://news.yandex.ru/Moscow/index.rss")  # Посква
    elif index == 'Псков' or index == 'псков':
        feed = feedparser.parse("https://news.yandex.ru/Pskov/index.rss")  # Псков
    elif index == 'мир' or index == 'в мире':
        feed = feedparser.parse("https://news.yandex.ru/world.rss")  # в мире

    full_text = ''
    next_n = [
        'Перейдём к следующей новости. - ',
        'Далее. - ',
        'Следующая новость. - ',
        'Далее по списку. - ',
        'К другим новостям. - '
    ]
    i = 0
    for entry in feed.entries[0:10]:
        summary = html.unescape(entry.summary)
        # f'Новость опубликована {str(entry.published)}.'
        if i < 9:
            full_text += f'{summary} {random.choice(next_n)} '
        else:
            full_text += f'{summary} Пока это все новости из данной категории. '
        i += 1
    cat = f'Озвучиваю новости из категории "{index}".\n'
    await say_it(ctx, text=cat + full_text)
    await ctx.send(cat)


async def say_it(ctx, *, text):
    if text is None:
        return
    if ctx.voice_client is None:
        return
    dt = Delorean()
    filename = f'{dt.epoch}_{str(ctx.guild.id)}.opus'
    source = await voice_synthesis(text, filename)

    if ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        while not bot.is_closed() and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            await asyncio.sleep(1)
        ctx.voice_client.pause()
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
    else:
        ctx.voice_client.pause()
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Недостаточно полномочий.')

bot.run(TOKEN)
