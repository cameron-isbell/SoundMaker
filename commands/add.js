const { SlashCommandBuilder } = require('discord.js');
const ytdl = require('ytdl-core-discord');
const queue_handler = require('../common/queue_handler.js');

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
        if ( (link == null) || (!(link.startsWith('https://www.youtube.com')) && !(link.startsWith('www.youtube.com')) ))
        {
            await interaction.reply(`Invalid link '${link}'`);
            return;
        }

        //Defer reply while ytdl thinks
        await interaction.deferReply();
        let info = await ytdl.getInfo(link);
        await queue_handler.pushNewSong(info);

        await interaction.editReply('Song successfully added!');
    },
};