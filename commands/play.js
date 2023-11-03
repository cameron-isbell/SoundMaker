const { SlashCommandBuilder } = require('discord.js');
const { join } = require('node:path');
const queue_handler = require('../common/queue_handler.js');

const fs = require('fs');
const { 
    joinVoiceChannel, 
    createAudioPlayer, 
    createAudioResource,
    VoiceConnection, 
    VoiceConnectionStatus,
    AudioPlayerStatus } = require('@discordjs/voice');

const ytdl = require('ytdl-core-discord');
const { queue } = require('async');

function delay(ms) {
    return new Promise(resolve=>setTimeout(resolve, ms));
}

module.exports = 
{
    data : new SlashCommandBuilder()
        .setName('play')
        .setDescription(`Play a song from a youtube link`),

    async execute(interaction) 
    {
        if (interaction.guild == null || !interaction.guild.available)
        {
            console.log(`[ERROR] guild ${interaction.guild.id} is not available`);
            await interaction.reply(`ERROR: Guild is not defined`);
            return;
        }

        if (queue_handler.queueLen() == 0)
        {
            await interaction.reply(('ERROR: No items in queue. Add a song with /add command'));
            return;
        }

        await interaction.reply('Now playing all items in queue');

        //join the voice channel
        const member = interaction.guild.members.cache.get(interaction.member.user.id);
        const voiceChannel = member.voice.channel;

        if (global.connection === null) 
        {
            global.connection = joinVoiceChannel ({
                channelId: member.voice.channelId,
                guildId: interaction.guildId,
                adapterCreator: interaction.guild.voiceAdapterCreator,
            });
        }
        
        global.player = createAudioPlayer();
        global.connection.subscribe(global.player);

        while (queue_handler.queueLen() > 0)
        {
            if (global.player.state != AudioPlayerStatus.Playing)
            {
                let info = await queue_handler.popNextSong();
                let resource = createAudioResource(ytdl.chooseFormat(ytdl.filterFormats(info.formats, 'audioonly'), {audioCodec : 'opus', quality : 'highest'}).url);
                global.player.play(resource);
            }

            global.connection.on('stateChange', (oldState, newState) => {
                if(oldState.status === VoiceConnectionStatus.Ready && newState.status === VoiceConnectionStatus.Connecting)
                {
                    global.connection.configureNetworking();
                }
            }); 

            await delay(1000);
        }
    }, 
};
