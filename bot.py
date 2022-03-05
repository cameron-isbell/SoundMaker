#Author: cameron-isbell
#Date Created: 9/14/2021
#Date Last Updated: 3/1/2022

#A discord bot used to play audio with command prefix '>'
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

#a dicionary of queues. one for each guild that the bot is playing in
queue_dict = {}

#a dictionary for each thread associated with each guild
thrd_dict = {}

#a dictionary the audio for each guild. 
audio_dict = {}
stop = False

#A thread running to check the queue whenever audio is done playing
def check_queue(guild):
    global stop
    global audio_dict

    while not stop:
        audio = audio_dict[guild.id]
        queue = queue_dict[guild.id]

        while not audio is None and (audio.is_playing() or audio.is_paused) and not stop:
            time.sleep(1)
        
        if queue.__len__() > 0:
            info = queue.pop(0)

            #FFMPEG is responsible for actually playing audio. does not download, streams directly from youtube using the link from the queue
            FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            audio_dict[guild.id] = discord.utils.get(bot.voice_clients, guild=guild)
            audio_dict[guild.id].play(discord.FFmpegPCMAudio(info['formats'][0]['url'], **FFMPEG_OPTS))

#send a message to the console when the bot is ready
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))    

#Adds a song, if valid, to the queue to be played
@bot.command(name='play', aliases=['p'])
async def play(ctx, *args):
    global queue
    await ctx.send('Processing Request...')
    url = ""
    #connect the bot to the vc if possible
    
    #Just in case the guild is None for some reason
    if ctx.guild is None:
        await ctx.send('Fatal Error: ctx.guild = None. Song could not be played.')
        return 

    try:
        if (not ctx.voice_client):
            chnl = ctx.author.voice.channel
            vc = await chnl.connect()

    except AttributeError:
        await ctx.send('User is not in a voice channel.')
        return
    
    #TODO: less lazy solution
    try:
        url = args[0]
    except IndexError:
        await ctx.send('No link given.')
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
        #'format':'bestaudio/best', d
        ydl_info = youtube_dl.YoutubeDL({'format' : 'bestaudio/best', 'noplaylist':'True', 'cachedir' : 'False'})
        with ydl_info:
            info = ydl_info.extract_info(url, download=False)
    except youtube_dl.utils.DownloadError:
        await ctx.send('Unsupported URL %s' % url)
        return

    if not ctx.guild.id in queue_dict.keys():
        queue_dict[ctx.guild.id] = []

    queue_dict[ctx.guild.id].append(info)
    
    #Set a key at this position with no audio playing yet
    if not ctx.guild.id in audio_dict.keys():
        audio_dict[ctx.guild.id] = None

    #create a new thread for each guild
    if not ctx.guild.id in thrd_dict.keys():
        thrd_dict[ctx.guild.id] = threading.Thread(target=check_queue, args=(ctx.guild,))
        thrd_dict[ctx.guild.id].start()

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

    queue = queue_dict[ctx.guild.id]

    #idx-1 since the item currently playing has been already popped from the queue
    if idx-1 >= queue.__len__():
        await ctx.send('No item in the queue at index %s' % args[0])
        return

    removed = queue.pop(idx-1)
    await ctx.send('Successfully removed item %s at index %s.' % (removed[0]['title'], args[0]))

#pause the music
@bot.command(name='pause')
async def pause(ctx):
    audio = audio_dict[ctx.guild.id]
    if audio is None or not audio.is_playing():
        await ctx.send('No audio playing.')
        return

    audio.pause()

#Resume audio if it's paused
@bot.command(name='resume')
async def resume(ctx):
    audio = audio_dict[ctx.guild.id]
    if audio is None:
        await ctx.send('no audio playing.')
        return
    elif not audio.is_paused():
        await ctx.send('audio is not paused.')
        return 

    audio.resume()

#force bot to leave the voice channel
@bot.command(name='leave')
async def leave(ctx):
    audio = audio_dict[ctx.guild.id]
    if not ctx.voice_client:
        await ctx.send('not in a voice channel')
        return

    if not audio is None:
        audio.stop()
        
    await ctx.guild.voice_client.disconnect()

#skip to the next song in the playlist by stopping the current audio
@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    audio = audio_dict[ctx.guild.id]
    if not audio is None and (audio.is_playing() or audio.is_paused()):
        audio.stop()

@bot.command(name='clear')
async def clear(ctx):
    queue_dict[ctx.guild.id].clear()
    await ctx.send('Queue successfully cleared!')

@bot.command(name='queue')
async def queue_cmd(ctx):
    if not ctx.guild.id in queue_dict.keys():
        queue_dict[ctx.guild.id] = []
    
    queue = queue_dict[ctx.guild.id]
    msg = '```'
    for i in range(0, queue.__len__()):
        msg += str(i) + '. ' + queue[i]['title'] + '\n'
    msg += '```'
    
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
        '>queue: show all items in the queue', 
        'limitations: Cannot seek, cannot play age restricted videos'
    ]

    msg = '```\n'
    for disc in cmd_descriptions:
        msg += disc + '\n'
    msg += '\n```'

    await ctx.send(msg)

#"why isn't the bot running on its own thread in the background?" you may be wondering. because the pi that the bot runs on
#says no no to that. weird bug that makes the only way to kill the bot to ctrl+c it. 

#TODO: BOT WON'T RUN IN CERTAIN SERVERS
#BOT WILL RANDOMLY GET INCREDIBLY LAGGY
def start_bot():
    bot.run(os.getenv('TOKEN'))

start_bot()
