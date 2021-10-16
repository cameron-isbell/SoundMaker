from __future__ import unicode_literals
import discord
import os
import subprocess
import requests
import youtube_dl
import threading
import time
from dotenv import load_dotenv
from discord.ext.commands import Bot

load_dotenv()
bot = Bot(command_prefix='>')

lock_queue = False
queue = []
audio : discord.VoiceClient = None

#HANDLE OPUS FOR ME
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

#plays one song from the top of the queue
def handle_queue():
    global audio
    data = queue.pop(0)
    info = data[0]
    ctx = data[1]

    #extract info from the url, also checks if the url is valid on youtube
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    audio = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    audio.play(discord.FFmpegPCMAudio(info['formats'][0]['url'], **FFMPEG_OPTS))

#A thread running to check the queue whenever audio is done playing
def check_queue():
    while True:
        while (not audio is None and (audio.is_playing() or audio.is_paused())):
            time.sleep(1)
        if queue.__len__() > 0:
            handle_queue()

#send a message to the console when the bot is ready
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))    
    t = threading.Thread(target=check_queue)
    t.start()

@bot.command(name='play', aliases=['p'])
async def play(ctx, *args):
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

    #download the data used to play the song
    try:
        ydl_info = youtube_dl.YoutubeDL({'format':'bestaudio/best', 'noplaylist':'True'})
        with ydl_info:
            info = ydl_info.extract_info(url, download=False)
    except youtube_dl.utils.DownloadError:
        await ctx.send('Unsupported URL')
        return

    queue.append((info,ctx))

#Remove an item at a specific point in the queue
@bot.command(name='remove', aliases=['rm'])
async def remove(ctx, *args):
    temp = args[0]
    idx = int(temp)

    if idx == 0:
        await ctx.send('Cannot remove item at index 0. Use skip instead.')
        return

    if idx-1 >= queue.__len__():
        await ctx.send('No item in the queue at index ' + args[0])
        return

    removed = queue.pop(idx-1)
    await ctx.send('Successfully removed item.')

#pause the music
@bot.command(name='pause')
async def pause(ctx):
    if audio is None or not audio.is_playing():
        await ctx.send('No audio playing.')
        return

    audio.pause()

#If audio is paused, resume
@bot.command(name='resume')
async def resume(ctx):
    if audio is None:
        await ctx.send('No audio playing.')
        return
    elif not audio.is_paused():
        await ctx.send('Audio is not paused.')
        return 

    audio.resume()    

#force bot to leave the server
@bot.command(name='leave')
async def leave(ctx):
    #if bot is in a channel
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send('Not in a vc.')

@bot.command(name='skip',aliases=['s'])
async def skip(ctx):
    if not audio is None and (audio.is_playing() or audio.is_paused):
        audio.stop()

def start_bot():
    bot.run(os.getenv('TOKEN'))

start_bot()
