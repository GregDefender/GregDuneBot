import os
import asyncio
import discord
from discord.ext import commands
import time

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs for join-to-create voice channels and categories
HAGGA_JOIN_ID = 1371983984925347980
HAGGA_CATEGORY_ID = 1371981195717378119
DESERT_JOIN_ID = 1371983716578234461
DESERT_CATEGORY_ID = 1371981370137772114

# Maps user_id to the ID of the channel created for them
user_channels = {}

# Lock for channel creation to avoid race conditions
channel_creation_lock = asyncio.Lock()

# Cooldown time in seconds to avoid rapid duplicate creations per user
USER_COOLDOWN = 10
# Tracks user_id -> timestamp of last creation event
user_cooldowns = {}

@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()

    # Clean expired cooldowns
    expired = [uid for uid, ts in user_cooldowns.items() if now - ts > USER_COOLDOWN]
    for uid in expired:
        user_cooldowns.pop(uid, None)

    # Ignore if no channel change
    if before.channel == after.channel:
        return

    # Check if user left a dynamically created channel, and delete if empty
    if before.channel and before.channel.id in user_channels.values():
        # Only delete if channel is empty
        channel = bot.get_channel(before.channel.id)
        if channel and len(channel.members) == 0:
            try:
                await channel.delete()
            except Exception as e:
                print(f"Error deleting channel {channel.id}: {e}")
            # Remove channel from user_channels dict
            # Find the user who had this channel and remove them
            user_to_remove = None
            for user_id, chan_id in user_channels.items():
                if chan_id == before.channel.id:
                    user_to_remove = user_id
                    break
            if user_to_remove:
                user_channels.pop(user_to_remove, None)

    # If user just joined a join-to-create channel and not on cooldown
    if after.channel and after.channel.id in (HAGGA_JOIN_ID, DESERT_JOIN_ID):
        if member.id in user_cooldowns:
            # User is still on cooldown - ignore
            return

        # Acquire lock to avoid race condition during channel creation
        if channel_creation_lock.locked():
            return

        async with channel_creation_lock:
            category_id = HAGGA_CATEGORY_ID if after.channel.id == HAGGA_JOIN_ID else DESERT_CATEGORY_ID
            channel_name = "Hagga Basin Expedition" if after.channel.id == HAGGA_JOIN_ID else "Deep Desert Expedition"

            # If user already has a channel, move them there instead of creating new
            if member.id in user_channels:
                existing_channel = bot.get_channel(user_channels[member.id])
                if existing_channel:
                    await member.move_to(existing_channel)
                    return
                else:
                    # Channel missing? Remove from tracking
                    user_channels.pop(member.id, None)

            # Create new channel
            guild = member.guild
            category = discord.utils.get(guild.categories, id=category_id)
            new_channel = await guild.create_voice_channel(name=channel_name, category=category)
            
            # Track new channel per user
            user_channels[member.id] = new_channel.id
            user_cooldowns[member.id] = time.time()

            # Move user to new channel
            await member.move_to(new_channel)

bot.run(os.getenv("DISCORD_TOKEN"))
