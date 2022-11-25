const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    data : new SlashCommandBuilder()
        .setName('test')
        .setDescription('test description'),

    async execute(interaction) {
        await interaction.reply('This command was run by ${interaction.user.username}');
    },
};