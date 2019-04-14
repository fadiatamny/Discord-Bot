import discord
from discord.ext import commands
import asyncio
from YoutubeDLL import YTDLSource

#the music cog
class Music(commands.Cog):   

    def __init__(self, bot):
        self.volume = 0.5 
        self.bot = bot
        self.playlist = []                        
        
        #plays the playlist till empty
    @commands.command(name="play", aliases=['p'])
    async def play(self, ctx):   
        if not self.playlist:
            await ctx.send("Add songs to queue list to play them")
        else:
            if not ctx.voice_client.is_playing():
                while self.playlist:
                    if not ctx.voice_client.is_playing():
                        track = self.playlist.pop(0)
                        ctx.voice_client.play(track, after=lambda e: print('Player error: %s' % e) if e else None)
                        ctx.voice_client.source.volume = self.volume
                        async with ctx.typing():
                            await ctx.send('Now playing: {}'.format(track.title))

                await ctx.send("No more songs in the queue order. add more then play afterwards")

        #joins server
    @commands.command()
    async def join(self, ctx):

        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()

        #joins a chat room nstarts playing song given from string or url
    @commands.command(name='add', aliases=['a'])
    async def add(self, ctx, *, arg):
        
        if arg.startswith('http'):
            player = await YTDLSource.from_url(arg, loop=self.bot.loop)
        else:
            player = await YTDLSource.search(arg, loop=self.bot.loop)
        self.playlist.append(player)

        if not ctx.voice_client.is_playing():
            async with ctx.typing():
                await ctx.send('Added: {} to the list'.format(player.title) )
        
        #skips song in queue
    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):

        if not ctx.author.voice :
            return await ctx.send("You are not connected to a voice channel.")
        
        if self.playlist:
            ctx.voice_client.stop()
            await ctx.send("Skipped")
            while self.playlist:
                if not ctx.voice_client.is_playing():
                    track = self.playlist.pop(0)
                    ctx.voice_client.play(track, after=lambda e: print('Player error: %s' % e) if e else None)
                    ctx.voice_client.source.volume = self.volume
                    async with ctx.typing():
                        await ctx.send('Now playing: {}'.format(track.title))
            await ctx.send("No more songs in the queue order. add more then play afterwards")
        else:
            ctx.voice_client.stop()
            await ctx.send("No more songs - Stopped")

        #prints current queue
    @commands.command(name='queue', aliases=['q'])
    async def queue(self, ctx):
        s = "```\n"
        i = 1
        for track in self.playlist:
            s = s + str(i) + ". " + track.title + "\n"
            i = i+1
        s = s + "```"

        await ctx.send(s)
        
        #removes a song from queue with index
    @commands.command(name='remove', aliases=['r'])
    async def remove(self, ctx, index: int):

        if not ctx.author.voice :
            return await ctx.send("You are not connected to a voice channel.")

        if self.playlist:
            self.playlist.pop(index-1)
            await ctx.send("Removed")
        else:
            await ctx.send("Queue is empty")

        #sets the voice clients volume in %
    @commands.command(name='volume', aliases=['vol','v'])
    async def volumeLevel(self, ctx, volume: float):

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        self.volume = volume
        ctx.voice_client.source.volume = volume
        await ctx.send("Changed volume to {}%".format(volume))

        #stops the client from transmiting voice
    @commands.command(name='stop', aliases=['leave'])
    async def stop(self, ctx):

        self.playlist.clear()
        await ctx.voice_client.disconnect()

        #insure smooth switching.
    @join.before_invoke
    @play.before_invoke
    async def ensure_voice(self, ctx):

        if ctx.author.voice:    
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()
            elif ctx.voice_client.is_playing():
                if ctx.author.voice.channel != ctx.voice_client.channel:
                    ctx.voice_client.stop()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")