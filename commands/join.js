const { SlashCommandBuilder } = require('discord.js');
const { joinVoiceChannel } = require('@discordjs/voice');

module.exports = 
{
    data : new SlashCommandBuilder()
        .setName('join')
        .setDescription(`Command SoundMaker to join user's voice channel`),

    async execute(interaction) 
    {
        //const guild = client.guilds.cache.get(interaction.guildId);
        guild = interaction.guild;
        if (guild == null || !guild.available)
        {
            console.log(`[ERROR] guild ${interaction.guildId} is not available`);
            interaction.reply(`ERROR: Guild is not defined`);
            return;
        }

        const member = interaction.guild.members.cache.get(interaction.member.user.id);
        const voiceChannel = member.voice.channel;

        await interaction.reply(`This user is in ${voiceChannel.name}`);
        const connection = joinVoiceChannel ({
            channelId: voiceChannel.id,
            guildId: interaction.guildId,
            adapterCreator: voiceChannel.guild.voiceAdapterCreator,
        });
        
    },
};