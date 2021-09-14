import discord
import os
from dotenv import load_dotenv
from discord.ext.commands import Bot

load_dotenv()
bot = Bot(command_prefix='>')
queue = []

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.command(name='play')
async def play(ctx, *args):
    if (not ctx.voice_client):
        chnl = ctx.author.voice.channel
        await chnl.connect()
    
    #TODO: TIME AS SECOND ARGUMENT
    url = args[0]
    


    print(url)



@bot.command(name='leave')
async def leave(ctx):
    #if bot is in a channel
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send('Not in a vc.')

@bot.command(name='server', help='Fetches server info')
async def fetch_info(ctx):
    guild = ctx.guild
    await ctx.send(f'Server Name: {guild.name}')
    await ctx.send(f'Server Size: {len(guild.members)}')
    await ctx.send(f'Server Name: {guild.owner.display_name}')

bot.run(os.getenv('TOKEN'))