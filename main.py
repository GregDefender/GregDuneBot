import os
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Channel IDs
HAGGA_JOIN_ID = 1371983984925347980
HAGGA_CATEGORY_ID = 1371981195717378119
DESERT_JOIN_ID = 1371983716578234461
DESERT_CATEGORY_ID = 1371981370137772114

# Track dynamically created channels
created_channels = set()
channel_creation_lock = asyncio.Lock()

@bot.event
async def on_voice_state_update(member, before, after):
    # Skip if the event isn't a channel join
    if after.channel is None or before.channel == after.channel:
        return

    # Handle Hagga Basin join
    if after.channel.id == HAGGA_JOIN_ID:
        await handle_dynamic_channel(member, "Hagga Basin Expedition", HAGGA_CATEGORY_ID)

    # Handle Deep Desert join
    elif after.channel.id == DESERT_JOIN_ID:
        await handle_dynamic_channel(member, "Deep Desert Expedition", DESERT_CATEGORY_ID)

    # Check if user left a dynamically created channel
    if before.channel and before.channel.id in created_channels:
        # Wait a bit for Discord to update voice states properly
        await asyncio.sleep(5)

        # Refetch channel to get fresh state
        channel = bot.get_channel(before.channel.id)
        if channel is None:
            # Channel already deleted or doesn't exist
            created_channels.discard(before.channel.id)
            return

        # If no members left, delete the channel
        if len(channel.members) == 0:
            await channel.delete()
            created_channels.discard(channel.id)

async def handle_dynamic_channel(member, name, category_id):
    async with channel_creation_lock:
        guild = member.guild
        category = discord.utils.get(guild.categories, id=category_id)

        # Create the new voice channel
        new_channel = await guild.create_voice_channel(name=name, category=category)
        created_channels.add(new_channel.id)

        # Move the user into the new channel
        await member.move_to(new_channel)

bot.run(os.getenv("DISCORD_TOKEN"))
