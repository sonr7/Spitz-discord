import discord
import asyncio
import os
import youtube_dl

token = os.environ.get('DISCORD_BOT_TOKEN')

client = discord.Client()

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
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

@client.event
async def on_ready():
    print('起動しました')

@client.event
async def on_message(message):
    if message.content.startswith('#spitz:'):
        kasi = message.content.replace('#spitz:', '')
        with open(kasi) as kasii:
            kasiyaru = kasii.read()
        await message.channel.send(kasiyaru)
    elif message.content == '#leave':
        if message.guild.voice_client is None:
            await message.channel.send("おーっと、ボイスチャンネルにいないからできないようだ！")
            return
        await message.guild.voice_client.disconnect()
        await message.channel.send("バイバイ！")
    elif message.content.startswith('#p'):
        try:
            if message.author.voice is None:
                await message.channel.send('おーっと、ボイスチャンネルにいないからできないようだ！')
            if message.guild.voice_client is None:
                await message.author.voice.channel.connect()
            if message.guild.voice_client.is_playing():
                embed = discord.Embed(title = 'キュー')
                url = message.content[3:]
                players = await YTDLSource.from_url(url, loop = client.loop)
                queue_list.append(players)
                embed.add_field(name = players.title, value = 'by {}'.format(message.author.id), inline = False)
                await message.channel.send(embed = embed)
                if not message.guild.voice_client.is_playing():
                    player = queue_list[0]
                    queue_list.remove(player)
                    await message.channel.send('{} を再生するよ!'.format(player.title))
                    await message.guild.voice_client.play(player)
            url = message.content[3:]
            player = await YTDLSource.from_url(url, loop=client.loop)
            await message.channel.send('{} を再生！'.format(player.title))
            message.guild.voice_client.play(player)
            if message.content == '#np':
                if not message.guild.voice_client.is_playing():
                    await message.channel.send("おーっと、再生してないからできないようだ！")
                    return
                embed = discord.Embed(title = player.title, url = player)
                await message.channel.send(embed = embed)
        except youtube_dl.utils.DownloadError:
            await message.channel.send('NOT FOUND!')
    if message.content == '#loop' and message.guild.voice_client.is_playing():
        await message.channel.send('るーぷ！')
        async def play():
            while not message.guilod.voice_client.is_playing:
                await asyncio.sleep(0.1)
            while True:
                waiter = asyncio.Future()
                message.guild.voice_client.play(message.guild.voice_client.source, after=waiter.set_result) 
                await waiter
        play_task = client.loop.create_task(play())
        lost_message = await client.wait_for("message", check = lambda m: m.content == "#lost")
        play_task.cancel()
        await message.channel.send('るーぷ終了！')
    elif message.content == "#stop":
        if message.guild.voice_client is None:
            await message.channel.send("おーっと、ボイスチャンネルにいないからできないようだ！")
            return
        if not message.guild.voice_client.is_playing():
            await message.channel.send("おーっと、再生してないからできないようだ！")
            return
        message.guild.voice_client.stop()
        await message.channel.send("停止...")


client.run(token)
