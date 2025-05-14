import os
import time
import json
import asyncio
import discord
import openai
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True  # Required for on_message or command handling

bot = commands.Bot(command_prefix="!", intents=intents)

# --- CONFIG IDs ---
HAGGA_JOIN_ID = 1371983984925347980
HAGGA_CATEGORY_ID = 1371981195717378119
DESERT_JOIN_ID = 1371983716578234461
DESERT_CATEGORY_ID = 1371981370137772114
CHAT_CHANNEL_ID = 123456789012345678  # 👈 Replace this with your desired chat channel ID

# --- SETUP ---
openai.api_key = os.getenv("OPENAI_API_KEY")

user_channels = {}
user_cooldowns = {}
moving_users = set()
channel_creation_lock = asyncio.Lock()
USER_COOLDOWN = 10  # seconds

expedition_counters = {"hagga": 0, "desert": 0}


@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()

    # Cleanup cooldowns
    expired = [uid for uid, ts in user_cooldowns.items() if now - ts > USER_COOLDOWN]
    for uid in expired:
        user_cooldowns.pop(uid, None)

    if before.channel == after.channel:
        return

    if member.id in moving_users:
        return

    # Delete empty custom channels
    if before.channel and before.channel.id in user_channels.values():
        channel = bot.get_channel(before.channel.id)
        if channel and len(channel.members) == 0:
            try:
                await channel.delete()
            except Exception as e:
                print(f"Failed to delete channel {channel.id}: {e}")

            user_to_remove = None
            for user_id, chan_id in user_channels.items():
                if chan_id == before.channel.id:
                    user_to_remove = user_id
                    break
            if user_to_remove:
                user_channels.pop(user_to_remove, None)
                user_cooldowns.pop(user_to_remove, None)

    # Create a new channel if user joined a join-to-create channel
    if after.channel and after.channel.id in (HAGGA_JOIN_ID, DESERT_JOIN_ID):
        if member.id in user_cooldowns:
            return

        if channel_creation_lock.locked():
            return

        async with channel_creation_lock:
            category_id = HAGGA_CATEGORY_ID if after.channel.id == HAGGA_JOIN_ID else DESERT_CATEGORY_ID
            channel_name = "Hagga Basin Expedition" if after.channel.id == HAGGA_JOIN_ID else "Deep Desert Expedition"
            counter_key = "hagga" if after.channel.id == HAGGA_JOIN_ID else "desert"

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
                    user_channels.pop(member.id, None)

            guild = member.guild
            category = discord.utils.get(guild.categories, id=category_id)
            new_channel = await guild.create_voice_channel(name=channel_name, category=category)

            user_channels[member.id] = new_channel.id
            user_cooldowns[member.id] = time.time()
            expedition_counters[counter_key] += 1

            moving_users.add(member.id)
            try:
                await member.move_to(new_channel)
            finally:
                moving_users.discard(member.id)


@bot.command(name="chat")
async def chat_with_gpt(ctx, *, question: str):
    if ctx.channel.id != CHAT_CHANNEL_ID:
        return  # Ignore messages outside the allowed channel

    await ctx.trigger_typing()
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # You can also use "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful assistant in a Discord server."},
                {"role": "user", "content": question}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        await ctx.reply(answer)
    except Exception as e:
        print(f"Error: {e}")
        await ctx.reply("Something went wrong while contacting ChatGPT.")


bot.run(os.getenv("DISCORD_TOKEN"))
