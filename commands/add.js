const { SlashCommandBuilder } = require('discord.js');
const { guildId } = require("./../config.json");
const { joinVoiceChannel, createAudioResource } = require('@discordjs/voice');
const { queue } = require('async');
const ytdl = require('ytdl-core-discord');


module.exports = 
{
    data : new SlashCommandBuilder()
        .setName('add')
        .setDescription(`Add a song to SoundMaker's queue`)
        .addStringOption(option => 
            option.setName('link')
                .setDescription('Youtube link to source audio from')
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

        let info = await ytdl.getInfo(link);
        let formats = ytdl.filterFormats(info.formats, 'audioonly');
        let format = ytdl.chooseFormat(formats, {audioCodec : 'opus', quality : 'highest'})

        global.queue.push(info);
        await interaction.reply('Song successfully added!');
    },
};