const { SlashCommandBuilder } = require('discord.js');
const { guildId } = require("./../config.json");
const { joinVoiceChannel, createAudioPlayer } = require('@discordjs/voice');
const ytdl = require('ytdl-core');
const ffmpeg = require('ffmpeg.js');

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
        const link = interaction.options.getString('link');
        //const guild = client.guilds.cache.get(interaction.guildId);
        guild = interaction.guild;
        if (guild == null || !guild.available)
        {
            console.log(`[ERROR] guild ${interaction.guildId} is not available`);
            await interaction.reply(`ERROR: Guild is not defined`);
            return;
        }

        //join the voice channel
        const member = interaction.guild.members.cache.get(interaction.member.user.id);
        const voiceChannel = member.voice.channel;

        //await interaction.reply(`This user is in ${voiceChannel.name}`);
        const connection = joinVoiceChannel ({
            channelId: member.voice.channel.id,
            guildId: interaction.guildId,
            adapterCreator: voiceChannel.guild.voiceAdapterCreator,
        });
        
        //check link valid
        if ( !( (link != null) && (link.startsWith('https://www.youtube.com') || link.startsWith('www.youtube.com') ) ) )
        {
            await interaction.reply(`Invalid link '${link}'`)
            return;
        }
        interaction.reply('Song successfully received!');

        let info = await ytdl.getInfo(link);
        let format = ytdl.chooseFormat(ytdl.filterFormats(info.formats, 'audioonly'), { audioQuality: 'AUDIO_QUALITY_MEDIUM'});
        
        let url = format.url;
        let stream = ffmpeg({
            arguments: ["-i", url],
        });
        let player = createAudioPlayer(stream);
        player.play();

    }, 
};