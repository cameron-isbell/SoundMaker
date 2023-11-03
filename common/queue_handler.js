/*
* Queue handler takes care of all queue related commands
* to avoid global variable definitions
*/

module.exports.queue = [];

module.exports.pushNewSong = async function(song) 
{
    this.queue.push(song);
}

module.exports.popNextSong = async function() 
{
    return this.queue.pop(0);
}

module.exports.peekNextSong = async function() 
{
    if (this.queue.length > 0)
    {
        return this.queue.pop(0);
    }
}

module.exports.removeSong = async function(index) 
{
    if (index < this.queue.length)
    {
        return this.queue.pop(index);
    }
}

module.exports.queueLen = async function()
{
    return this.queue.length;
}

module.exports.getAllItems = async function()
{
    if (this.queue.length == 0)
    {
        return [];
    }
    return this.queue;
}
