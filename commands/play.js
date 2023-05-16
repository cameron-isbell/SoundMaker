const { SlashCommandBuilder } = require('discord.js');
const { guildId } = require("./../config.json");
const { join } = require('node:path');
const fs = require('fs');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, getVoiceConnection } = require('@discordjs/voice');
const ffmpeg = require('fluent-ffmpeg');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path
ffmpeg.setFfmpegPath(ffmpegPath)

const ytdl = require('ytdl-core');

const { create } = require('node:domain');
const output = require('fluent-ffmpeg/lib/options/output');
const { findSourceMap } = require('node:module');
const { downloadFromInfo } = require('ytdl-core');

module.exports = 
{
    data : new SlashCommandBuilder()
        .setName('play')
        .setDescription(`Play a song from a youtube link`)
        .addStringOption(option => 
            option.setName('link')
                .setDescription('A youtube link to play audio from')
                .setRequired(true)),

    async execute(interaction) 
    {
        if (interaction.guild == null || !interaction.guild.available)
        {
            console.log(`[ERROR] guild ${interaction.guild.id} is not available`);
            await interaction.reply(`ERROR: Guild is not defined`);
            return;
        }
        const link = interaction.options.getString('link');

        //handle invalid links
        if ( !( (link != null) && (link.startsWith('https://www.youtube.com') || link.startsWith('www.youtube.com') ) ) )
        {
            await interaction.reply(`Invalid link '${link}'`)
            return;
        }
        await interaction.reply('Song successfully received!');

        //join the voice channel
        const member = interaction.guild.members.cache.get(interaction.member.user.id);
        const voiceChannel = member.voice.channel;

        const connection = joinVoiceChannel ({
            channelId: member.voice.channelId,
            guildId: interaction.guildId,
            adapterCreator: interaction.guild.voiceAdapterCreator,
        });

        const player = createAudioPlayer();
        connection.subscribe(player);

        //const filename = join(__dirname, 'fire.mp3');
        let info = await ytdl.getInfo(link);

        ytdl(link, {format : 'mp3', filter : 'audioonly', quality : 'lowest'}).pipe(fs.createWriteStream(join(__dirname, 'audiofiles/downloaded.mp3')))
        .on('close', () => {
            console.log('ytdl closed');
            ffmpeg(join(__dirname, 'audiofiles/downloaded.mp3'))
            .toFormat('opus')
            .audioCodec('libopus')
            .on('error', (err) => {
                console.log('An error occurred: ' + err.message);
            })
            .on('progress', (progress) => {
                console.log('Processing: ' + progress.targetSize + ' KB converted');
            })
            .on('end', () => {
                console.log('Processing finished !');
                let resource = createAudioResource(join(__dirname, 'audiofiles/output.opus'));
                player.play(resource);
            })
            .save(join(__dirname, 'audiofiles/output.opus'));
        });
    }, 
};
