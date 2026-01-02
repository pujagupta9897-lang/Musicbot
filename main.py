import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get bot token from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot instance with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Event: Bot ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot latency: {bot.latency}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# Event: Member join
@bot.event
async def on_member_join(member):
    print(f'{member} has joined the server')

# Event: Member remove
@bot.event
async def on_member_remove(member):
    print(f'{member} has left the server')

# Basic ping command
@bot.command(name='ping')
async def ping(ctx):
    """Responds with the bot's latency"""
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# Help command
@bot.command(name='help')
async def help_command(ctx):
    """Displays available commands"""
    embed = discord.Embed(
        title='Music Bot Help',
        description='List of available commands:',
        color=discord.Color.blue()
    )
    embed.add_field(name='!ping', value='Check bot latency', inline=False)
    embed.add_field(name='!help', value='Display this help message', inline=False)
    await ctx.send(embed=embed)

# Load cogs from cogs directory
async def load_cogs():
    """Load all cogs from the cogs directory"""
    cogs_dir = 'cogs'
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Loaded cog: {filename}')
                except Exception as e:
                    print(f'Failed to load cog {filename}: {e}')

# Setup hook - runs when bot connects
async def setup_hook():
    """Setup hook for loading cogs"""
    await load_cogs()

bot.setup_hook = setup_hook

# Main entry point
if __name__ == '__main__':
    if not TOKEN:
        print('ERROR: DISCORD_TOKEN not found in environment variables!')
        print('Please create a .env file with DISCORD_TOKEN=your_token_here')
        exit(1)
    
    try:
        print('Starting Music Bot...')
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print('ERROR: Invalid token provided!')
        exit(1)
    except Exception as e:
        print(f'ERROR: {e}')
        exit(1)
