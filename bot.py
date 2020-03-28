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


@bot.command(name='?')
async def custom_help_command(ctx):
    author = ctx.message.author

    embed = discord.Embed(
        colour=discord.Colour.green()
    )

    embed.set_author(name='Команды оленя:')
    embed.add_field(name='!?', value='Выводит доступные команды', inline=True)
    embed.add_field(name='!олень', value='Только попробуй назвать его оленем!', inline=True)
    embed.add_field(name='!кости', value='Кинуть кости (!кости <кол-во сторон> <не обязательно: кол-во костей>', inline=True)
    await ctx.send_message(author, embed=embed)


@bot.command(name='олень')
async def deer(ctx):
    response = 'Сам олень!'
    await ctx.send(response)


@bot.command(name='кости')
async def roll(ctx, number_of_sides: int, number_of_dice: int = 1):
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
