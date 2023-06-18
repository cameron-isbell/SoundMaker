const { SlashCommandBuilder } = require('discord.js');
const { guildId } = require("./../config.json");
const { join } = require('node:path');
const fs = require('fs');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, getVoiceConnection, VoiceConnection, VoiceConnectionStatus } = require('@discordjs/voice');
const ytdl = require('ytdl-core-discord');

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

        if (global.queue.length == 0)
        {
            await interaction.reply(('ERROR: No items in queue. Add a song with /add command'));
            return;
        }

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

        if (global.player == null)
        {
            global.player = createAudioPlayer();
        }
        global.connection.subscribe(global.player);

        while (global.queue.length > 0)
        {
            let info = global.queue[0];
            let resource = createAudioResource(ytdl.chooseFormat(ytdl.filterFormats(info.formats, 'audioonly'), {audioCodec : 'opus', quality : 'highest'}).url);
            
            global.player.play(resource);
            console.log(info);
            await interaction.reply(`Now playing "${info.videoDetails.title}"`);

            global.connection.on('stateChange', (oldState, newState) => {
                if(oldState.status === VoiceConnectionStatus.Ready && newState.status === VoiceConnectionStatus.Connecting)
                {
                    global.connection.configureNetworking();
                }
            });

            // while (global.player.state != AudioPlayerStatus.Idle)
            // {

            // }
        }
    }, 
};
