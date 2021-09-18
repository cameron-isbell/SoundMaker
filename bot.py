from __future__ import unicode_literals
import discord
import os
import subprocess
import requests
import youtube_dl
from dotenv import load_dotenv
from discord.ext.commands import Bot

load_dotenv()
bot = Bot(command_prefix='>')

queue = []
audio : discord.VoiceClient = None

OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']
def load_opus(opus_libs=OPUS_LIBS):
    if opus.is_loaded():
        return True

    for opus_lib in opus_libs:
        try:
            opus.load_opus(opus_lib)
            return
        except OSError:
            pass

        raise RuntimeError('Could not load an opus lib. Tried %s' % (', '.join(opus_libs)))

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

def on_done_playing(arg):
    print('x')

@bot.command(name='play', aliases=['p'])
async def play(ctx, *args):
    global audio
    global queue

    #connect the bot to the vc if possible
    try:
        if (not ctx.voice_client):
            chnl = ctx.author.voice.channel
            vc = await chnl.connect()

    except AttributeError:
        await ctx.send('User is not in a voice channel.')
        return
    
    #check if we've received a url
    try:
        url = args[0]
    except IndexError:
        await ctx.send('No song given.')
        return
    
    #check that the url is valid
    try:
        if (requests.get(url).status_code != 200):
            await ctx.send('Invalid url.')
            return
    except requests.exceptions.ConnectionError:
        await ctx.send('Invalid url.')
        return

    #extract info from the url, also checks if the url is valid on youtube
    try:
        ydl_info = youtube_dl.YoutubeDL({'format':'bestaudio/best', 'noplaylist':'True'})
        with ydl_info:
            info = ydl_info.extract_info(url, download=False)
    except youtube_dl.utils.DownloadError:
        await ctx.send('Unsupported URL')
        return

    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    audio = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    audio.play(discord.FFmpegPCMAudio(info['formats'][0]['url'], **FFMPEG_OPTS), after=on_done_playing)

@bot.command(name='leave')
async def leave(ctx):
    #if bot is in a channel
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send('Not in a vc.')

@bot.command(name='skip',aliases=['s'])
async def skip(ctx):
    try:
        if (audio.is_playing()):
            audio.stop()
    #just in case audio is never set
    except AttributeError:
        await ctx.send('No audio playing')

bot.run(os.getenv('TOKEN'))