#bot.py

import os
import random
import discord

from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()
TOKEN = os.environ.get('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')


@bot.event
async def on_ready():
    print('Bot is ready.')


@bot.command(name='хелп')
async def custom_help(ctx, command=''):
    embed = discord.Embed(
        colour=discord.Colour.green()
    )
    # I was to lazy to write an array
    # commands = [
    #    '!хелп'
    # ]
    if command == '':
        embed.add_field(name='!хелп', value='Выводит доступные команды', inline=False)
        embed.add_field(name='!олень', value='Только попробуй назвать его оленем!', inline=False)
        embed.add_field(name='!кинь', value='!кинь <кол-во сторон> [кол-во костей]', inline=False)

        await ctx.send('Команды', embed=embed)


@bot.command(name='олень')
async def deer(ctx):
    response = 'Сам олень!'
    await ctx.send(response)


@bot.command(name='кинь')
async def roll(ctx, number_of_sides: int = 20, number_of_dice: int = 1):
    if 1 < number_of_sides <= 100 and 0 < number_of_dice <= 50:
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
