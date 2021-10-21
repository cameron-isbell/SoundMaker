from __future__ import unicode_literals
import discord
import os
import requests
import youtube_dl
import threading
import time
from dotenv import load_dotenv
from discord.ext.commands import Bot

load_dotenv()
bot = Bot(command_prefix='>')

queue = []
audio = None

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
    
    try:
        url = args[0]
    except IndexError:
        await ctx.send('No link given.')
        return        
    
    url = args[0]
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

    embed = discord.Embed(
        title=info['title'],
            url = info['url'],
            description=info['description'],
            color=discord.Color.blue())

    embed.set_author(name=info['uploader'])
    embed.set_thumbnail(url=info['thumbnail'])
    embed.set_footer(text='Song is added to the queue.')

    await ctx.send(embed=embed)

#Remove an item at a specific point in the queue
@bot.command(name='remove', aliases=['rm'])
async def remove(ctx, *args):
    idx = int(args[0])

    if idx == 0:
        await ctx.send('Cannot remove item at index 0. Use skip instead.')
        return

    #idx-1 since the item currently playing has been already popped from the queue
    if idx-1 >= queue.__len__():
        await ctx.send('No item in the queue at index %s' % args[0])
        return

    removed = queue.pop(idx-1)
    await ctx.send('Successfully removed item %s at index %s.' % (removed[0]['title'], args[0]))

#pause the music
@bot.command(name='pause')
async def pause(ctx):
    if audio is None or not audio.is_playing():
        await ctx.send('No audio playing.')
        return

    audio.pause()

#Resume audio if it's paused
@bot.command(name='resume')
async def resume(ctx):
    if audio is None:
        await ctx.send('no audio playing.')
        return
    elif not audio.is_paused():
        await ctx.send('audio is not paused.')
        return 

    audio.resume()

#force bot to leave the server
@bot.command(name='leave')
async def leave(ctx):
    if not ctx.voice_client:
        await ctx.send('not in a voice channel')
        return

    await ctx.guild.voice_client.disconnect()

@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    if not audio is None and (audio.is_playing() or audio.is_paused()):
        audio.stop()

@bot.command(name='clear')
async def clear(ctx):
    queue.clear()
    await ctx.send('Queue successfully cleared!')

@bot.command(name='queue')
async def queue_cmd(ctx):
    msg = '`'
    for i in range(0, queue.__len__()):
        msg += str(i) + '. ' + queue[i][0]['title'] + '\n'
    msg += '`'
    
    if queue.__len__() == 0:
        msg = '`Empty`'

    await ctx.send(msg)

@bot.command(name='commands')
async def commands(ctx):
    cmd_descriptions = [
        '>commands: prints this message',
        '>play: plays a song from a given youtube link',
        '>skip: if a song is playing, move onto the next song in the queue or, if the queue is empty, ends the currently playing song',
        '>pause: pauses a song',
        '>resume: if the song is paused, resume it',
        '>leave: make SoundMaker leave the voice channel it is in',
        '>remove: remove a song from the queue at the given index',
        '>clear: remove all items in the queue',
        '>queue: show all items in the queue'
    ]

    msg = '`'
    for disc in cmd_descriptions:
        msg += disc + '\n'
    msg += '`'

    await ctx.send(msg)

#TODO: add a thread to run the bot on. then, have main check for command line input to end the program
def start_bot():
    bot.run(os.getenv('TOKEN'))

start_bot()
