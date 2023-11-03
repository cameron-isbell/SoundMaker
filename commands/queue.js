const { SlashCommandBuilder } = require('discord.js');
const queue_handler = require('../common/queue_handler.js');

module.exports = {
    data : new SlashCommandBuilder()
        .setName('queue')
        .setDescription('test description'),
        
    async execute(interaction) {
        if (queue_handler.queueLen() == 0)
        {
            await interaction.reply('No items in the queue');
        }
        else
        {
            let queueLen = await queue_handler.queueLen();
            let queue = await queue_handler.getAllItems();

            if (queueLen == 0)
            {
                await interaction.reply('Empty');
            }
            else 
            {
                let songList = '';
                for (let i = 0; i < queueLen; i++)
                {
                    songList += queue[i].videoDetails.title + '\n';
                }
                await interaction.reply(`${songList}`);
            }
        }
    },
};