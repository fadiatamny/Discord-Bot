import discord
from discord.ext import commands
import random
import youtube_dl
import asyncio
import logging
import datetime

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
            self.playing = False
            self.playlist = [] 
            self.volume = 1

        @commands.command()
        async def join(self, ctx, *, channel: discord.VoiceChannel):

            if ctx.voice_client is not None:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            else:
                await ctx.author.voice.channel.connect()

        @commands.command(name='play', aliases=['playhere', 'joinplay'])
        async def play(self, ctx, *, arg):
            print('\n-------------------------\n')
            print(ctx.voice_client) 
            print('\n-------------------------\n')
            print('\n'+str(datetime.datetime.now()))
            print('inital list:')
            print(self.playlist)
            print('client status : ')
            print(ctx.voice_client.is_playing())
            
            if not ctx.voice_client.is_playing():
                if not self.playlist:
                    if arg.startswith('http'):
                        async with ctx.typing():
                            self.playlist.append(await YTDLSource.from_url(arg, loop=self.bot.loop))
                    else:
                        async with ctx.typing():
                            self.playlist.append(await YTDLSource.search(arg, loop=self.bot.loop))

                else:
                    if arg.startswith('http'):
                        async with ctx.typing():
                            player = await YTDLSource.from_url(arg, loop=self.bot.loop)
                    else:
                        async with ctx.typing():
                            player = await YTDLSource.search(arg, loop=self.bot.loop)
                    self.playlist.append(player)


                print('after edit list:')
                print(self.playlist)

                track = self.playlist.pop(0)
                ctx.voice_client.play(track, after=lambda e: print('Player error: %s' % e) if e else None)
                await ctx.send('Now playing: {}'.format(track.title))

                print('after playing list:')
                print(self.playlist)
                print('client status after playing : ')
                print(ctx.voice_client.is_playing())

            else:
                if arg.startswith('http'):
                    async with ctx.typing():
                        player = await YTDLSource.from_url(arg, loop=self.bot.loop)
                else:
                    async with ctx.typing():
                        player = await YTDLSource.search(arg, loop=self.bot.loop)
                self.playlist.append(player)


        @commands.command()
        async def volume(self, ctx, volume: float):
            if ctx.voice_client is None:
                return await ctx.send("Not connected to a voice channel.")

            ctx.voice_client.source.volume = volume
            await ctx.send("Changed volume to {}%".format(volume))

        @commands.command(name='stop', aliases=['leave'])
        async def stop(self, ctx):
            await ctx.voice_client.disconnect()

        #insure smooth switching.
        @play.before_invoke
        async def ensure_voice(self, ctx):
            if ctx.voice_client is None:
                if ctx.author.voice:
                    print("here")
                    await ctx.author.voice.channel.connect()
                else:
                    await ctx.send("You are not connected to a voice channel.")
                    raise commands.CommandError("Author not connected to a voice channel.")
            elif ctx.voice_client.is_playing():
                ctx.voice_client.stop()


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