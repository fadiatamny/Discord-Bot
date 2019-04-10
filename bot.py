import discord
from discord.ext import commands
import random
import youtube_dl
import asyncio
import logging
import time


youtube_dl.utils.bug_reports_message = lambda: ''


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

    # Placeholder
    @classmethod
    async def search(cls, search, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):   

        def __init__(self, bot):
            self.bot = bot
            self.playlist = [] 
            self.volume = 1
            
        @commands.command()
        async def func(self, ctx):        
            while self.playlist:
                if not ctx.voice_client.is_playing():
                    track = self.playlist.pop(0)
                    ctx.voice_client.play(track, after=lambda e: print('Player error: %s' % e) if e else None)
                    async with ctx.typing():
                        await ctx.send('Now playing: {}'.format(track.title))
            return

        @commands.command()
        async def join(self, ctx):

            if ctx.voice_client is not None:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            else:
                await ctx.author.voice.channel.connect()

        @commands.command(name='play', aliases=['p'])
        async def play(self, ctx, *, arg):

            if not ctx.voice_client.is_playing():
                if not self.playlist:
                    if arg.startswith('http'):
                        self.playlist.append(await YTDLSource.from_url(arg, loop=self.bot.loop))
                    else:
                        self.playlist.append(await YTDLSource.search(arg, loop=self.bot.loop))
                    func(ctx)

            else:
                if arg.startswith('http'):
                    player = await YTDLSource.from_url(arg, loop=self.bot.loop)
                else:
                    player = await YTDLSource.search(arg, loop=self.bot.loop)
                self.playlist.append(player)
                async with ctx.typing():
                    await ctx.send('Added: {} to the list'.format(player.title) )
                return

            return
                
        @commands.command(name='skip', aliases=['s'])
        async def skip(self, ctx):
            if ctx.voice_client is None:
                return await ctx.send("Not connected to a voice channel.")

            if self.playlist:
                ctx.voice_client.stop()
                func(ctx)
                await ctx.send("skipped")
            else:
                ctx.voice_client.stop()
                await ctx.send("No more songs - Stopped")

            return

        @commands.command(name='volume', aliases=['vol'])
        async def volume(self, ctx, volume: float):
            if ctx.voice_client is None:
                return await ctx.send("Not connected to a voice channel.")

            self.volume = volume
            ctx.voice_client.source.volume = volume
            await ctx.send("Changed volume to {}%".format(volume))

            return

        @commands.command(name='stop', aliases=['leave'])
        async def stop(self, ctx):
            self.playlist.clear()
            await ctx.voice_client.disconnect()

            return

        #insure smooth switching.
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

            return


#initialize Bot enviroment 

#token = input('Bot Token:')
token = "testtoken.txt"
btoken = open(token, "r").read() 

description = 'Tragicly organize Tragic'
prefix = '.'
token = btoken

bot = commands.Bot(command_prefix=prefix, description=description)

@bot.event
async def on_ready():
    print('Logged in as {0} {1}'.format(bot.user.id,bot.user.name))
    print('------')


bot.add_cog(Music(bot))
bot.run(token)