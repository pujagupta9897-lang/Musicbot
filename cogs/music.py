import discord
from discord.ext import commands
import wavelink
from wavelink.ext import spotify
from typing import Optional, Union
import asyncio


class Music(commands.Cog):
    """Music cog with YouTube and Wavelink integration."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wavelink: wavelink.Client = wavelink.Client(client=bot)
        bot.add_app_command(self.wavelink)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        """Event fired when a Node is ready for requests."""
        print(f"Wavelink Node: {node.identifier} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason) -> None:
        """Event fired when a track ends."""
        if player.queue.is_empty:
            return

        next_track = await player.play(player.queue.get())
        embed = discord.Embed(
            title="Now Playing",
            description=f"[{next_track.title}]({next_track.uri})",
            color=discord.Color.purple()
        )
        embed.add_field(name="Duration", value=f"{next_track.length // 60000}:{next_track.length % 60000 // 1000:02d}")
        embed.add_field(name="Author", value=next_track.author, inline=False)
        
        await player.home.send(embed=embed)

    async def ensure_voice(self, ctx: commands.Context) -> Optional[wavelink.Player]:
        """Ensure user is in a voice channel and bot is connected."""
        if not ctx.author.voice:
            embed = discord.Embed(
                description="❌ You must be connected to a voice channel!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return None

        player: wavelink.Player = ctx.voice_client

        if player is None:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
                player.home = ctx.channel
            except discord.ClientException as e:
                embed = discord.Embed(
                    description=f"❌ Failed to connect: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return None

        return player

    @commands.command(
        name="play",
        aliases=["p"],
        description="Play a song from YouTube"
    )
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Play a track from YouTube."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        async with ctx.typing():
            tracks = await wavelink.YouTubeTrack.search(query)

            if not tracks:
                embed = discord.Embed(
                    description=f"❌ No tracks found for `{query}`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            track = tracks[0]
            await player.queue.put_wait(track)

            if not player.is_playing():
                await player.play(player.queue.get())
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{track.title}]({track.uri})",
                    color=discord.Color.purple()
                )
                embed.add_field(name="Duration", value=f"{track.length // 60000}:{track.length % 60000 // 1000:02d}")
                embed.add_field(name="Author", value=track.author)
                embed.add_field(name="Queue Position", value="1", inline=False)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="✅ Added to Queue",
                    description=f"[{track.title}]({track.uri})",
                    color=discord.Color.green()
                )
                embed.add_field(name="Position", value=f"#{len(player.queue)}")
                embed.add_field(name="Duration", value=f"{track.length // 60000}:{track.length % 60000 // 1000:02d}")
                await ctx.send(embed=embed)

    @commands.command(name="playtop", description="Play a song at the top of the queue")
    async def playtop(self, ctx: commands.Context, *, query: str) -> None:
        """Play a track at the top of the queue."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        async with ctx.typing():
            tracks = await wavelink.YouTubeTrack.search(query)

            if not tracks:
                embed = discord.Embed(
                    description=f"❌ No tracks found for `{query}`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            track = tracks[0]
            
            # Insert at the beginning of queue
            player.queue._queue.appendleft(track)
            
            if not player.is_playing():
                await player.play(player.queue.get())

            embed = discord.Embed(
                title="✅ Added to Top of Queue",
                description=f"[{track.title}]({track.uri})",
                color=discord.Color.green()
            )
            embed.add_field(name="Position", value="#1")
            await ctx.send(embed=embed)

    @commands.command(name="skip", aliases=["s"], description="Skip the current track")
    async def skip(self, ctx: commands.Context) -> None:
        """Skip the current track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_playing():
            embed = discord.Embed(
                description="❌ No track is currently playing",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        current = player.current
        await player.skip()

        embed = discord.Embed(
            title="⏭️ Skipped",
            description=f"Skipped: [{current.title}]({current.uri})",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="queue", aliases=["q"], description="View the current queue")
    async def queue(self, ctx: commands.Context, page: int = 1) -> None:
        """View the current queue."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if len(player.queue) == 0:
            embed = discord.Embed(
                description="📭 Queue is empty",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        items_per_page = 10
        pages = (len(player.queue) + items_per_page - 1) // items_per_page

        if page > pages or page < 1:
            embed = discord.Embed(
                description=f"❌ Invalid page number. Total pages: {pages}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ""
        for i, track in enumerate(list(player.queue)[start:end], start=start + 1):
            duration = f"{track.length // 60000}:{track.length % 60000 // 1000:02d}"
            queue_list += f"`{i}.` [{track.title}]({track.uri}) `{duration}`\n"

        embed = discord.Embed(
            title="🎵 Queue",
            description=queue_list or "No tracks in this page",
            color=discord.Color.purple()
        )
        
        if player.current:
            embed.add_field(
                name="Currently Playing",
                value=f"[{player.current.title}]({player.current.uri})",
                inline=False
            )

        embed.set_footer(text=f"Page {page}/{pages} | Total tracks: {len(player.queue)}")
        await ctx.send(embed=embed)

    @commands.command(name="pause", description="Pause the current track")
    async def pause(self, ctx: commands.Context) -> None:
        """Pause the current track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if player.is_paused():
            embed = discord.Embed(
                description="❌ Track is already paused",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        await player.pause(True)

        embed = discord.Embed(
            title="⏸️ Paused",
            description=f"Paused: [{player.current.title}]({player.current.uri})",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="resume", aliases=["r"], description="Resume the paused track")
    async def resume(self, ctx: commands.Context) -> None:
        """Resume the paused track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_paused():
            embed = discord.Embed(
                description="❌ No paused track to resume",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        await player.pause(False)

        embed = discord.Embed(
            title="▶️ Resumed",
            description=f"Resumed: [{player.current.title}]({player.current.uri})",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="stop", description="Stop the music and clear the queue")
    async def stop(self, ctx: commands.Context) -> None:
        """Stop the music and clear the queue."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        await player.stop()
        player.queue.clear()

        embed = discord.Embed(
            title="⏹️ Stopped",
            description="Music stopped and queue cleared",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="leave", aliases=["disconnect", "dc"], description="Disconnect the bot from voice channel")
    async def leave(self, ctx: commands.Context) -> None:
        """Disconnect the bot from the voice channel."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        await player.disconnect()

        embed = discord.Embed(
            description="👋 Disconnected from voice channel",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="now", aliases=["current", "np"], description="Show the currently playing track")
    async def now(self, ctx: commands.Context) -> None:
        """Show the currently playing track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_playing():
            embed = discord.Embed(
                description="❌ No track is currently playing",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        track = player.current
        position = player.position
        duration = track.length

        progress_bar = self._create_progress_bar(position, duration)

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.purple()
        )
        embed.add_field(name="Author", value=track.author)
        embed.add_field(name="Duration", value=f"{duration // 60000}:{duration % 60000 // 1000:02d}")
        embed.add_field(name="Progress", value=progress_bar, inline=False)
        embed.add_field(name="Position in Queue", value=f"1/{len(player.queue) + 1}")
        await ctx.send(embed=embed)

    @commands.command(name="seek", description="Seek to a specific position in the current track")
    async def seek(self, ctx: commands.Context, seconds: int) -> None:
        """Seek to a specific position in the current track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_playing():
            embed = discord.Embed(
                description="❌ No track is currently playing",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if seconds < 0 or seconds * 1000 > player.current.length:
            embed = discord.Embed(
                description=f"❌ Invalid seek position. Track duration: {player.current.length // 1000} seconds",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        await player.seek(seconds * 1000)

        embed = discord.Embed(
            title="⏩ Seeked",
            description=f"Seeked to {seconds // 60}:{seconds % 60:02d}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="volume", aliases=["vol", "v"], description="Set the player volume (0-100)")
    async def volume(self, ctx: commands.Context, volume: int) -> None:
        """Set the player volume."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if volume < 0 or volume > 100:
            embed = discord.Embed(
                description="❌ Volume must be between 0 and 100",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        await player.set_volume(volume)

        embed = discord.Embed(
            title="🔊 Volume Changed",
            description=f"Volume set to {volume}%",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="remove", description="Remove a track from the queue by position")
    async def remove(self, ctx: commands.Context, position: int) -> None:
        """Remove a track from the queue."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if len(player.queue) == 0:
            embed = discord.Embed(
                description="❌ Queue is empty",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if position < 1 or position > len(player.queue):
            embed = discord.Embed(
                description=f"❌ Invalid position. Queue has {len(player.queue)} tracks",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        track = player.queue._queue[position - 1]
        del player.queue._queue[position - 1]

        embed = discord.Embed(
            title="🗑️ Removed from Queue",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="clear", description="Clear the entire queue")
    async def clear(self, ctx: commands.Context) -> None:
        """Clear the queue."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if len(player.queue) == 0:
            embed = discord.Embed(
                description="❌ Queue is already empty",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        player.queue.clear()

        embed = discord.Embed(
            title="🧹 Queue Cleared",
            description="All tracks have been removed from the queue",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, ctx: commands.Context) -> None:
        """Shuffle the queue."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if len(player.queue) == 0:
            embed = discord.Embed(
                description="❌ Queue is empty",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        player.queue.shuffle()

        embed = discord.Embed(
            title="🔀 Queue Shuffled",
            description=f"Shuffled {len(player.queue)} tracks",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="loop", description="Loop the current track or queue")
    async def loop(self, ctx: commands.Context, mode: str = "track") -> None:
        """Set loop mode for the current track or queue."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        mode = mode.lower()
        if mode not in ["track", "queue", "off"]:
            embed = discord.Embed(
                description="❌ Invalid loop mode. Use: `track`, `queue`, or `off`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if mode == "track":
            player.queue.mode = wavelink.QueueMode.loop
            message = "🔂 Track looping enabled"
        elif mode == "queue":
            player.queue.mode = wavelink.QueueMode.loop_all
            message = "🔁 Queue looping enabled"
        else:
            player.queue.mode = wavelink.QueueMode.normal
            message = "➡️ Looping disabled"

        embed = discord.Embed(
            title="Loop Mode",
            description=message,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="search", description="Search for a track without playing it")
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        """Search for tracks."""
        async with ctx.typing():
            tracks = await wavelink.YouTubeTrack.search(query)

            if not tracks:
                embed = discord.Embed(
                    description=f"❌ No tracks found for `{query}`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            results = ""
            for i, track in enumerate(tracks[:10], 1):
                duration = f"{track.length // 60000}:{track.length % 60000 // 1000:02d}"
                results += f"`{i}.` [{track.title}]({track.uri}) `{duration}`\n"

            embed = discord.Embed(
                title=f"🔍 Search Results for '{query}'",
                description=results,
                color=discord.Color.purple()
            )
            embed.set_footer(text="Use !play [track name] to play")
            await ctx.send(embed=embed)

    @commands.command(name="lyrics", description="Get lyrics for the current track")
    async def lyrics(self, ctx: commands.Context) -> None:
        """Get lyrics for the current track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_playing():
            embed = discord.Embed(
                description="❌ No track is currently playing",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🎵 Lyrics",
            description=f"Lyrics feature coming soon for [{player.current.title}]({player.current.uri})",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="info", description="Get information about the current track")
    async def info(self, ctx: commands.Context) -> None:
        """Get information about the current track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_playing():
            embed = discord.Embed(
                description="❌ No track is currently playing",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        track = player.current
        duration = f"{track.length // 60000}:{track.length % 60000 // 1000:02d}"

        embed = discord.Embed(
            title="ℹ️ Track Information",
            color=discord.Color.purple()
        )
        embed.add_field(name="Title", value=track.title, inline=False)
        embed.add_field(name="Author", value=track.author)
        embed.add_field(name="Duration", value=duration)
        embed.add_field(name="URL", value=f"[Click Here]({track.uri})", inline=False)
        embed.add_field(name="Isrc", value=track.isrc or "N/A")
        await ctx.send(embed=embed)

    @commands.command(name="rewind", description="Rewind the track by 10 seconds")
    async def rewind(self, ctx: commands.Context, seconds: int = 10) -> None:
        """Rewind the current track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_playing():
            embed = discord.Embed(
                description="❌ No track is currently playing",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        new_position = max(0, player.position - (seconds * 1000))
        await player.seek(new_position)

        embed = discord.Embed(
            title="⏪ Rewind",
            description=f"Rewound by {seconds} seconds",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="forward", description="Forward the track by 10 seconds")
    async def forward(self, ctx: commands.Context, seconds: int = 10) -> None:
        """Forward the current track."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if not player.is_playing():
            embed = discord.Embed(
                description="❌ No track is currently playing",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        new_position = min(player.current.length, player.position + (seconds * 1000))
        await player.seek(new_position)

        embed = discord.Embed(
            title="⏩ Forward",
            description=f"Forwarded by {seconds} seconds",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="playing", description="Check if the bot is playing music")
    async def playing(self, ctx: commands.Context) -> None:
        """Check if the bot is playing music."""
        player = await self.ensure_voice(ctx)
        if not player:
            return

        if player.is_playing():
            status = "▶️ Playing"
        elif player.is_paused():
            status = "⏸️ Paused"
        else:
            status = "⏹️ Stopped"

        embed = discord.Embed(
            title="Player Status",
            description=status,
            color=discord.Color.blue()
        )
        if player.current:
            embed.add_field(
                name="Current Track",
                value=f"[{player.current.title}]({player.current.uri})",
                inline=False
            )
        await ctx.send(embed=embed)

    def _create_progress_bar(self, current: int, total: int, bar_length: int = 20) -> str:
        """Create a progress bar for the track."""
        if total == 0:
            percent = 0
        else:
            percent = current / total

        filled = int(bar_length * percent)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        current_time = f"{current // 60000}:{current % 60000 // 1000:02d}"
        total_time = f"{total // 60000}:{total % 60000 // 1000:02d}"
        
        return f"`{bar}` {current_time}/{total_time}"


async def setup(bot: commands.Bot) -> None:
    """Setup the music cog."""
    await bot.add_cog(Music(bot))
