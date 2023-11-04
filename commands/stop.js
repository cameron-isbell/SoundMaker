const { SlashCommandBuilder } = require('discord.js');

module.exports = 
{
    data : new SlashCommandBuilder()
        .setName('stop')
        .setDescription(`Stop playing the current song`),

    async execute(interaction) 
    {
        if (interaction.guild == null || !interaction.guild.available)
        {
            console.log(`[ERROR] guild ${interaction.guild.id} is not available`);
            await interaction.reply(`ERROR: Guild is not defined`);
            return;
        }

        if (global.player == null)
        {
            await interaction.reply('No song is currently playing');
            return;
        }

        global.player.stop();
        interaction.reply('Stopped playing');
    },
};