import os
import time
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Channel ID of the "Join to Create" voice channel
Hagga_Basin_JOIN_TO_CREATE_CHANNEL_ID = 1371983984925347980
Hagga_Basin_TEMP_CHANNEL_CATEGORY_ID = 1371981195717378119
Deep_Desert_JOIN_TO_CREATE_CHANNEL_ID = 1371983716578234461
Deep_Desert_TEMP_CHANNEL_CATEGORY_ID = 1371981370137772114
created_channels = {}


@bot.event
async def on_voice_state_update(member, before, after):
    # User joins the "Join to Create" channel for Hagga Basin
    if after.channel and after.channel.id == Hagga_Basin_JOIN_TO_CREATE_CHANNEL_ID:
        guild = member.guild
        category = discord.utils.get(guild.categories,
                                     id=Hagga_Basin_TEMP_CHANNEL_CATEGORY_ID)

        # Create the new voice channel
        new_channel = await guild.create_voice_channel(
            name="Hagga Basin Expedition",
            category=category  #,
            #user_limit=5  # Optional: Limit number of users
        )

        # Move the user to the new channel
        await member.move_to(new_channel)

        # Track created channel
        created_channels[member.id] = new_channel.id

    # User joins the "Join to Create" channel for Deep Desert
    if after.channel and after.channel.id == Deep_Desert_JOIN_TO_CREATE_CHANNEL_ID:
        guild = member.guild
        category = discord.utils.get(guild.categories,
                                     id=Deep_Desert_TEMP_CHANNEL_CATEGORY_ID)

        # Create the new voice channel
        new_channel = await guild.create_voice_channel(
            name="Deep Desert Expedition",
            category=category  #,
            #user_limit=5  # Optional: Limit number of users
        )

        # Move the user to the new channel
        await member.move_to(new_channel)

        # Track created channel
        created_channels[member.id] = new_channel.id

    # Check if any created channels are now empty and delete them
    time.sleep(1)
    for user_id, channel_id in list(created_channels.items()):
        channel = bot.get_channel(channel_id)
        if channel and len(channel.members) == 0:
            await channel.delete()
            del created_channels[user_id]



bot.run(os.getenv("DISCORD_TOKEN"))
