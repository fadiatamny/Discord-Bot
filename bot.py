import discord
from discord.ext import commands
import random
import youtube_dl
import asyncio
import logging
import time



youtube_dl.utils.bug_reports_message = lambda: ''

#init youtube and ffmpg  options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'outtmpl': './cache/%(title)s.%(ext)s'   
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

#the youtubedll class
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def search(cls, search, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

#the music cog
class Music(commands.Cog):   

        def __init__(self, bot):
            self.volume = 0.5 
            self.bot = bot
            self.playlist = []                        
            
            #plays the playlist till empty
        @commands.command(name="play", aliases=['p'])
        async def play(self, ctx):   

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


#initialize Bot enviroment 

token = input('Bot Token:')
btoken = open(token, "r").read() 

description = 'Tragicly organize Tragic'
prefix = '.'
token = btoken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


bot = commands.Bot(command_prefix=prefix, description=description)

@bot.event
async def on_ready():
    print('Logged in as {0} {1}'.format(bot.user.id,bot.user.name))
    print('------')


bot.add_cog(Music(bot))
bot.run(token)
