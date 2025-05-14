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

created_channels = set()
channel_creation_lock = asyncio.Lock()

# Track users recently handled to prevent duplicate channel creation
user_cooldowns = {}

COOLDOWN_SECONDS = 10  # Adjust as needed


@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()

    # Clean up cooldown dict for expired entries
    to_remove = [user_id for user_id, timestamp in user_cooldowns.items() if now - timestamp > COOLDOWN_SECONDS]
    for user_id in to_remove:
        user_cooldowns.pop(user_id, None)

    if after.channel == before.channel:
        return

    # If user is in cooldown, skip creating a channel again
    if member.id in user_cooldowns:
        return

    if after.channel and after.channel.id == HAGGA_JOIN_ID:
        if channel_creation_lock.locked():
            return

        async with channel_creation_lock:
            await handle_dynamic_channel(member, "Hagga Basin Expedition", HAGGA_CATEGORY_ID)
            user_cooldowns[member.id] = time.time()

    elif after.channel and after.channel.id == DESERT_JOIN_ID:
        if channel_creation_lock.locked():
            return

        async with channel_creation_lock:
            await handle_dynamic_channel(member, "Deep Desert Expedition", DESERT_CATEGORY_ID)
            user_cooldowns[member.id] = time.time()

    if before.channel and before.channel.id in created_channels:
        channel = bot.get_channel(before.channel.id)
        if channel is None:
            created_channels.discard(before.channel.id)
            return

        if len(channel.members) == 0:
            await channel.delete()
            created_channels.discard(channel.id)


async def handle_dynamic_channel(member, name, category_id):
    guild = member.guild
    category = discord.utils.get(guild.categories, id=category_id)

    new_channel = await guild.create_voice_channel(name=name, category=category)
    created_channels.add(new_channel.id)

    await member.move_to(new_channel)


bot.run(os.getenv("DISCORD_TOKEN"))
