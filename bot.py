import discord
from discord import EntityType, PrivacyLevel
from discord.ext import commands
from dotenv import load_dotenv
import os
import user_message_parser
from datetime import datetime, timezone, timedelta
import pytz

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')  # Your bot token from .env file

# Intents are required for the bot to interact with the server
intents = discord.Intents.default()  # Adjust intents as needed
intents.guild_scheduled_events = True  # Ensures the bot can connect to guilds
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix="<3", intents=intents)

#Given event data, will check if event exists
async def get_event(ctx, event_data):
    guild = ctx.guild  # Access the guild (server) where the command is invoked
    if not guild:
        await ctx.send("This command can only be used in a guild.")
        return
    guild_events = await guild.fetch_scheduled_events()
    # for event in guild_events:
    #     if(event.location == event_data["location"] and (event.end_time == event_data["start_time"] or event.start_time == event_data["end_time"])):
    #         return event
    for event in guild_events:
        # Match event based on name, start_time, and location
        if (
            event.name == event_data["event_name"]
            and event.start_time == datetime.fromisoformat(event_data["start_time"]).replace(tzinfo=timezone.utc)
            and (event.location).lower() == event_data["location"].lower()
        ):
            return event
    return None


async def get_event_to_update(ctx, event_data):
    guild = ctx.guild  # Access the guild (server) where the command is invoked
    if not guild:
        await ctx.send("This command can only be used in a guild.")
        return

    guild_events = await guild.fetch_scheduled_events()

    # Parse start and end times from event_data
    new_start_time = datetime.fromisoformat(event_data["start_time"]).replace(tzinfo=timezone.utc)
    new_end_time = datetime.fromisoformat(event_data["end_time"]).replace(tzinfo=timezone.utc)
    location = event_data["location"].lower()
    add_description = event_data["description"]
    # Define the local timezone (e.g., New York/Atlanta)
    local_tz = pytz.timezone("America/New_York")

    # Localize the new event times to the local timezone
    new_start_local = new_start_time.astimezone(local_tz)
    new_end_local = new_end_time.astimezone(local_tz)
    new_event_date = new_start_local.date()

    # Iterate through the events to find a matching one based on location and overlapping times
    for event in guild_events:
        # Localize the existing event's times to the local timezone
        event_start_local = event.start_time.astimezone(local_tz)
        event_end_local = event.end_time.astimezone(local_tz)
        event_date = event_start_local.date()  # Date of the existing event

        # print("current event being looked at", event_date)
        # print("the date of the event trying to add", new_event_date)

        # Ensure the new event's date matches or accounts for midnight crossover
        if not (event_date == new_event_date or
                (new_start_local.time() > new_end_local.time() and new_event_date == event_date - timedelta(days=1))):
            continue  # Skip this event if the dates do not align

        if event.location and event.location.lower() == location:
            # Check if the event times overlap or are adjacent
            if ((event_start_local <= new_start_local <= event_end_local) or  # New event starts within the current event time range
                (event_start_local <= new_end_local <= event_end_local) or  # New event ends within the current event time range
                (new_start_local <= event_start_local and new_end_local >= event_end_local)):  # New event fully encompasses the current one
                # If the times overlap or are adjacent, extend the event's time range
                updated_start_time = min(event.start_time, new_start_time)
                updated_end_time = max(event.end_time, new_end_time)

                # Return the event with updated times
                return event, {
                    "location": location,
                    "description": add_description,
                    "start_time": updated_start_time,
                    "end_time": updated_end_time
                }

            # If there's a gap, append the new description without updating the time
            if new_start_time > event.end_time or new_end_time < event.start_time:
                return event, {"description": add_description}

    # If no event is found to update
    return None



@bot.command(name="bot_help")
async def bot_help(ctx):
    guild = ctx.guild  # Access the guild (server) where the command is invoked
    if not guild:
        await ctx.send("This command can only be used in a guild.")
        return
    await ctx.send('''Hello, this is hoangyen's shitty event scheduler: Event Scheduler Slay! I was really lazy to do basic checks so here are the rules:
                    1. Please do not use 12am. The bot hates it and GPT nor I could figure it out. If your event ends at 12am, please but 11:45pm ty.
                    Also, the time is EST. (hardcoded sry)
                    2. Use "<3" to ask the bot to create/update your booking event
                    3. Two functions for you to use:
                        a) <3schedule_event, will schedule an event. DOES NOT LOOK FOR EXISTING EVENTS
                        b) <3update_event, parses through your input and uses {location, date_of_event} as a unique identifier for event. Title of event is not unique/doesn't matter
                    4. Example input: 
                    The following bookings "STUDY SLAY" have been confirmed:

                    Space Information
                    Location: Georgia Tech Library Spaces
                    Space: Price Gilbert 2216
                    Date: Sunday, November 17, 2024
                    Time: 6:00pm - 8:00pm

                    Please note if you are booking a room for immediate use that it takes approximately 5-10 minutes from the time you book to the time when your card will be recognized at the door. If you've booked in advance, there should be no issue.

                    If you have any trouble accessing the rooms, please contact the INFO Desk on the Grove Level of Price Gilbert Memorial Library, via phone at 404.894.4500, or via chat on Ask Us!

                    You are required to check in to your room on the display. If you do not check in within 10 minutes of your reservation, your reservation will be cancelled, and someone could book that room.

                    Check In Code: P7T4
                    4. TY EVERYONE
                    ''')

#testing
@bot.command()
async def test(ctx, arg):
    if arg == 'hi':
        arg = 'bye'
    await ctx.send(arg)

@bot.command(name="get_events")
async def get_events(ctx):
    guild = ctx.guild  # Access the guild (server) where the command is invoked
    if not guild:
        await ctx.send("This command can only be used in a guild.")
        return
    
    try:
        # Fetch the scheduled events for the guild
        events = await guild.fetch_scheduled_events()

        # If there are no events, let the user know
        if not events:
            await ctx.send("There are no upcoming events for this guild.")
            return

        # Format and send the events as a message
        event_list = "\n".join([f"**{event.name}**\nStart: {event.start_time.strftime('%A, %B %d, %Y at %I:%M %p')}\nEnd: {event.end_time.strftime('%A, %B %d, %Y at %I:%M %p')}\nLocation: {event.location or 'No location specified'}\n" for event in events])
        await ctx.send(f"**Upcoming Events for {guild.name}:**\n{event_list}")
    
    except discord.Forbidden:
        await ctx.send("I don't have permission to view events for this guild.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while fetching events: {e}")

    
@bot.command(name="schedule_event")
async def schedule_event(ctx, *, arg):
    guild = ctx.guild  # Access the guild (server) where the command is invoked
    if not guild:
        await ctx.send("This command can only be used in a guild.")
        return

    try:
        # Parse event data using your custom parser
        event_data = user_message_parser.get_event_parameters_from_GT(arg)

        # Convert ISO 8601 strings to timezone-aware datetime objects
        start_time = datetime.fromisoformat(event_data["start_time"])
        end_time = datetime.fromisoformat(event_data["end_time"])

        entity_type = EntityType.external
        privacy_level = PrivacyLevel.guild_only
        # Create the scheduled event
        scheduled_event = await guild.create_scheduled_event(
            name=event_data["event_name"],
            description=event_data["description"],
            start_time=start_time,
            end_time=end_time,
            entity_type=entity_type,
            privacy_level=privacy_level,
            location=event_data["location"]  # Required for external events
        )

        # Send a success message
        await ctx.send(f"Scheduled Event Created: {scheduled_event.name}\nURL: {scheduled_event.url}")

    except discord.Forbidden:
        await ctx.send("I don't have permission to manage events.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to create event: {e}")

@bot.command(name="update_event")
async def update_event(ctx, *, arg):
    guild = ctx.guild  # Access the guild (server) where the command is invoked
    if not guild:
        await ctx.send("This command can only be used in a guild.")
        return

    try:
        # Get the event to update and updated event data
        result = await get_event_to_update(ctx, user_message_parser.get_event_parameters_from_GT(arg))
        if result is None:
            await ctx.send("I found no event to update. To update the time of an event, the time must come directly after or before the original time.")
            return
        
        current_event, updated_event_data = result

        # Extract the date from the current event's start_time
        current_event_date = current_event.start_time.date()

        # print("current event:", current_event, current_event_date)
        # print("updated event data", updated_event_data)
        updated_description = f'{current_event.description}\n{updated_event_data["description"]}'

        # print("new description to add", updated_description)
        sorted_description = user_message_parser.sort_event_description(updated_description)
        # print("sorted_description",sorted_description)
        # check if only the description needs updating
        if "description" in updated_event_data and len(updated_event_data) == 1:
            await current_event.edit(description=sorted_description)
            await ctx.send(f'Event description updated: \n{sorted_description}. \nTo update the discord event time, make sure there are no gaps in your booking!')
            return
        

        # if no gaps exist in the description, parse the times and update the Discord event

        print("sorted_description", sorted_description)

        # Parse time slots from the sorted description
        time_slots = user_message_parser.parse_event_times_from_description(sorted_description)
        if not time_slots:
            # print("time_slots is None")
            return

        # Find the largest continuous interval
        largest_interval = user_message_parser.find_largest_continuous_interval(time_slots)
        if not largest_interval:
            await ctx.send("Could not determine the largest continuous interval.")
            return

        earliest_start_time, latest_end_time = largest_interval

        # Handle timezone and date localization
        local_tz = pytz.timezone("America/New_York")
        earliest_start_date = current_event.start_time.date()
        latest_end_date = current_event.start_time.date()

        # Adjust dates if the event spans past midnight
        if latest_end_time < earliest_start_time:
            latest_end_date += timedelta(days=1)  # End time is on the next day

        # Combine the date and time
        earliest_start_datetime = datetime.combine(earliest_start_date, earliest_start_time.time())
        latest_end_datetime = datetime.combine(latest_end_date, latest_end_time.time())

        # Localize to the event's timezone
        earliest_start_localized = local_tz.localize(earliest_start_datetime)
        latest_end_localized = local_tz.localize(latest_end_datetime)

        # Convert localized times to UTC
        earliest_start_utc = earliest_start_localized.astimezone(timezone.utc)
        latest_end_utc = latest_end_localized.astimezone(timezone.utc)

        # Determine if we need to update the event time
        gap_in_description = user_message_parser.check_description_for_gaps(sorted_description)
        if gap_in_description:
            await current_event.edit(description=sorted_description)
            await ctx.send(f'Event description updated with sorted times: \n{sorted_description} Discord event time remains unchanged due to a gap.')
        else:
            await current_event.edit(
                start_time=earliest_start_utc,
                end_time=latest_end_utc,
                description=sorted_description
            )
            await ctx.send(f"Scheduled Event Updated: {current_event.name}\nURL: {current_event.url}\nUpdated Time: {earliest_start_time.strftime('%I:%M %p')} - {latest_end_time.strftime('%I:%M %p')}")

    except discord.Forbidden:
        await ctx.send("I don't have permission to manage events.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to update event: {e}")

# Event to confirm the bot is connected
@bot.event
async def on_ready():
    print(f"Bot is connected as {bot.user} (ID: {bot.user.id})")
    print("Connected to the following servers:")
    for guild in bot.guilds:
        print(f" - {guild.name} (ID: {guild.id})")

# Run the bot
bot.run(TOKEN)
