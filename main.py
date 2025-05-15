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

HAGGA_JOIN_ID = 1371983984925347980
HAGGA_CATEGORY_ID = 1371981195717378119
DESERT_JOIN_ID = 1371983716578234461
DESERT_CATEGORY_ID = 1371981370137772114

user_channels = {}  # user_id -> channel_id
user_cooldowns = {}  # user_id -> timestamp cooldown
channel_creation_lock = asyncio.Lock()

# This set tracks users currently being moved by the bot
moving_users = set()

USER_COOLDOWN = 10  # seconds


@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()

    # Cleanup cooldowns
    expired = [uid for uid, ts in user_cooldowns.items() if now - ts > USER_COOLDOWN]
    for uid in expired:
        user_cooldowns.pop(uid, None)

    # Ignore if no channel change
    if before.channel == after.channel:
        return

    # Ignore updates caused by the bot moving the user to avoid loops
    if member.id in moving_users:
        return

    # Handle user leaving a dynamic channel — delete if empty
    if before.channel and before.channel.id in user_channels.values():
        channel = bot.get_channel(before.channel.id)
        if channel and len(channel.members) == 0:
            try:
                await channel.delete()
            except Exception as e:
                print(f"Failed to delete channel {channel.id}: {e}")

            # Remove from tracking dict (find user by channel)
            user_to_remove = None
            for user_id, chan_id in user_channels.items():
                if chan_id == before.channel.id:
                    user_to_remove = user_id
                    break
            if user_to_remove:
                user_channels.pop(user_to_remove, None)
                user_cooldowns.pop(user_to_remove, None)

    # If user joins the join-to-create channel and not on cooldown
    if after.channel and after.channel.id in (HAGGA_JOIN_ID, DESERT_JOIN_ID):
        if member.id in user_cooldowns:
            return

        if channel_creation_lock.locked():
            return

        async with channel_creation_lock:
            category_id = HAGGA_CATEGORY_ID if after.channel.id == HAGGA_JOIN_ID else DESERT_CATEGORY_ID
            channel_name = "Hagga Basin Expedition" if after.channel.id == HAGGA_JOIN_ID else "Deep Desert Expedition"

            # If user already has a channel, move them there
            if member.id in user_channels:
                existing_channel = bot.get_channel(user_channels[member.id])
                if existing_channel:
                    moving_users.add(member.id)
                    try:
                        await member.move_to(existing_channel)
                    finally:
                        moving_users.discard(member.id)
                    return
                else:
                    # Remove invalid channel reference
                    user_channels.pop(member.id, None)

            # Create new channel and move user
            guild = member.guild
            category = discord.utils.get(guild.categories, id=category_id)
            new_channel = await guild.create_voice_channel(name=channel_name, category=category)

            user_channels[member.id] = new_channel.id
            user_cooldowns[member.id] = time.time()

            moving_users.add(member.id)
            try:
                await member.move_to(new_channel)
            finally:
                moving_users.discard(member.id)


bot.run(os.getenv("DISCORD_TOKEN"))
