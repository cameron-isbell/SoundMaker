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
import guild_queue as gq
from dotenv import load_dotenv
from discord.ext.commands import Bot

load_dotenv()
bot = Bot(command_prefix='>')

#a dicionary of queues. one for each guild that the bot is playing in
queue_dict = {}
stop = False

#A thread running to check the queue whenever audio is done playing
def check_queue(guild):
    global stop
    global queue_dict

    while not stop:
        audio = queue_dict[guild.id].audio
        queue = queue_dict[guild.id].queue

        if (not audio is None and (audio.is_playing() or audio.is_paused())):
            time.sleep(1)
            continue
        
        if queue.__len__() > 0:
            info = queue.pop(0)

            #FFMPEG is responsible for actually playing audio. does not download, streams directly from youtube using the link from the queue
            FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -preset ultrafast'}
            
            queue_dict[guild.id].audio = discord.utils.get(bot.voice_clients, guild=guild)
            queue_dict[guild.id].audio.play(discord.FFmpegPCMAudio(info['formats'][0]['url'], **FFMPEG_OPTS))

#send a message to the console when the bot is ready
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))    

#Adds a song, if valid, to the queue to be played
@bot.command(name='play', aliases=['p'])
async def play(ctx, *args):
    global queue_dict
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
            await chnl.connect()
            
    except AttributeError:
        await ctx.send('User is not in a voice channel.')
        return
    
    if args.__len__() != 1:
        await ctx.send('Incorrect # arguments. Please only give me a link.')
        return
        
    url = args[0]
    link_start = ['https://www.youtube.com', 'www.youtube.com']
    valid = False
    for start in link_start:
        if url.startswith(start):
            valid = True
            break
    
    if not valid:
        await ctx.send('Must be a youtube link')
        return

    #download the data used to play the song
    try:
        ydl_info = youtube_dl.YoutubeDL({'format' : 'bestaudio', 'noplaylist':'True', 'cachedir' : 'False'})
        with ydl_info:
            info = ydl_info.extract_info(url, download=False)
    except youtube_dl.utils.DownloadError:
        await ctx.send('Unsupported URL %s' % url)
        return

    #each key in the queue dictionary is the id of the server
    #each item in the queue dictionary is a Guild_Queue_Item storing info needed to play the song, such as
    #the check_queue thread
    #the audio currently playing
    #the queue of items to still be played

    if not ctx.guild.id in queue_dict.keys():
        queue_dict[ctx.guild.id] = gq.Guild_Queue_Item(threading.Thread(target=check_queue, args=(ctx.guild,)))
        queue_dict[ctx.guild.id].thread.start()

    queue_dict[ctx.guild.id].add_song(info)

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
    global queue_dict
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
    global queue_dict
    if not ctx.guild.id in queue_dict.keys():
        await ctx.send('No audio playing.')
        return

    audio = queue_dict[ctx.guild.id].audio
    if audio is None or not audio.is_playing():
        await ctx.send('No audio playing.')
        return

    audio.pause()

#Resume audio if it's paused
@bot.command(name='resume')
async def resume(ctx):
    global queue_dict
    if not ctx.guild.id in queue_dict.keys():
        await ctx.send('No songs have been played in this server since last reboot.')
        return

    audio = queue_dict[ctx.guild.id].audio
    if audio is None:
        await ctx.send('No audio currently playing.')
        return
    elif not audio.is_paused():
        await ctx.send('Audio is not paused.')
        return 

    audio.resume()

#force bot to leave the voice channel
@bot.command(name='leave')
async def leave(ctx):
    global queue_dict
    if not ctx.voice_client:
        await ctx.send('Not in a voice channel.')
        return

    audio = queue_dict[ctx.guild.id].audio
    if not audio is None:
        audio.stop()
        
    await ctx.guild.voice_client.disconnect()

#skip to the next song in the playlist by stopping the current audio
@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    global queue_dict
    if not ctx.guild.id in queue_dict.keys():
        await ctx.send('No songs have been played in this server since last reboot.')
        return

    audio = queue_dict[ctx.guild.id].audio
    if not audio is None and (audio.is_playing() or audio.is_paused()):
        audio.stop()
        await ctx.send('Skipped!')

@bot.command(name='clear')
async def clear(ctx):
    global queue_dict
    if not ctx.guild.id in queue_dict.keys():
        await ctx.send('Queue has not been initialized yet.')
        return

    queue_dict[ctx.guild.id].queue.clear()
    await ctx.send('Queue successfully cleared!')

@bot.command(name='queue')
async def queue_cmd(ctx):
    global queue_dict

    queue = []
    if ctx.guild.id in queue_dict.keys():
        queue = queue_dict[ctx.guild.id].queue

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
