import discord
from discord.ext import tasks, commands
import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
import os
from dotenv import load_dotenv


load_dotenv()

# Replace this with your bot token
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.guild_scheduled_events = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store reminders we've already sent
reminded_events = set()

def is_work_hour(now):
    return (
        0 <= now.weekday() <= 4 and
        now.hour < 17
    )

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    check_events.start()

@tasks.loop(minutes=30)
async def check_events():
    now = datetime.datetime.now(ZoneInfo("Europe/London"))

    # 💣 Kill the bot if after 17:00 UK time
    if not is_work_hour(now):
        print("🔴 Workday over. Shutting down bot to save Railway hours.")
        os._exit(0)

    for guild in bot.guilds:
        try:
            events = await guild.fetch_scheduled_events()
            for event in events:
                if event.start_time:
                    time_until = event.start_time - now

                    # Reminder 1 hour before
                    if datetime.timedelta(hours=1) <= time_until <= datetime.timedelta(hours=1, minutes=30):
                        key = f"{event.id}-1h"
                        if key not in reminded_events:
                            await send_reminder(event, "1 hour")
                            reminded_events.add(key)

                    # Reminder 1 day before
                    elif datetime.timedelta(days=1) <= time_until <= datetime.timedelta(days=1, minutes=30):
                        key = f"{event.id}-1d"
                        if key not in reminded_events:
                            await send_reminder(event, "1 day")
                            reminded_events.add(key)

        except Exception as e:
            print(f"❌ Error checking events for {guild.name}: {e}")

async def send_reminder(event, when):
    # Try to find a channel named 'general'
    channel = discord.utils.get(event.guild.text_channels, name="general")
    message = f"@everyone ⏰ Reminder: **{event.name}** is starting in {when}!"

    if channel:
        await channel.send(message)
    elif event.guild.system_channel:
        await event.guild.system_channel.send(message)
    else:
        print(f"⚠️ No suitable channel found in {event.guild.name}")

bot.run(TOKEN)
