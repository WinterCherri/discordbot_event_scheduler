import re
from datetime import datetime, timezone, timedelta, date
import pytz


'''

Parses through user email of booking confirmation and returns a hashmap of information

*************Example string input*************

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


'''
def get_event_parameters_from_GT(message: str):

    event_name_match = re.search(r'The following bookings "(.*?)" have been confirmed:', message)
    event_name = event_name_match.group(1) if event_name_match else None

    location_match = re.search(r'Space: (.+)', message)
    location = location_match.group(1) if location_match else None
    
    # Extract Check-in Code
    checkin_code_match = re.search(r'Check In Code: (.+)', message)
    checkin_code = checkin_code_match.group(1) if checkin_code_match else None

    date_match = re.search(r'Date: [A-Za-z]+, ([A-Za-z]+ \d{1,2}, \d{4})', message)
    time_match = re.search(r'Time: (\d{1,2}:\d{2}[apm]+) - (\d{1,2}:\d{2}[apm]+)', message)
    
    if not date_match or not time_match:
        raise ValueError("Invalid input format")
    
    # Extract date and times
    date = date_match.group(1)  # e.g., "November 17, 2024"
    start_time = time_match.group(1)  # e.g., "6:00pm"
    end_time = time_match.group(2)  # e.g., "8:00pm"

    # Combine date and time into datetime objects
    start_datetime = datetime.strptime(f"{date} {start_time}", "%B %d, %Y %I:%M%p")
    end_datetime = datetime.strptime(f"{date} {end_time}", "%B %d, %Y %I:%M%p")
    
    # Localize datetime to a specific timezone (e.g., 'America/New_York')
    local_tz = pytz.timezone("America/New_York")  # Replace with your timezone
    start_datetime = local_tz.localize(start_datetime)  # Attach local timezone
    end_datetime = local_tz.localize(end_datetime)
    
    # Convert to UTC
    start_datetime_utc = start_datetime.astimezone(timezone.utc)
    end_datetime_utc = end_datetime.astimezone(timezone.utc)

    # Convert to ISO 8601 format
    start_iso = start_datetime_utc.isoformat()  # e.g., "2024-11-17T23:00:00Z"
    end_iso = end_datetime_utc.isoformat()      # e.g., "2024-11-18T01:00:00Z"
    
    formatted_start_time = start_datetime.strftime("%I:%M%p")  # Capital AM/PM
    formatted_end_time = end_datetime.strftime("%I:%M%p")      # Capital AM/PM
    description = f'{formatted_start_time} - {formatted_end_time}: {checkin_code}'
    
    return {
        "event_name": event_name,
        "location": location,
        "description": description,
        "start_time": start_iso,
        "end_time": end_iso
    }

def check_description_for_gaps(event_description):
    '''

    Takes in a string(event description) and outputs a hashmap of an gap(what makes the times not continuous)

    '''
    # This regular expression matches time periods and their associated check-in codes
    time_pattern = r'(\d{1,2}:\d{2}[apm]+) - (\d{1,2}:\d{2}[apm]+): (\S+)'

    # Find all the time ranges and associated check-in codes in the description
    time_slots = re.findall(time_pattern, event_description)
    # Convert times to datetime objects
    time_slots_with_dt = []
    for start_time_str, end_time_str, code in time_slots:
        # Parse times using the correct format
        start_time = datetime.strptime(start_time_str, "%I:%M%p")
        end_time = datetime.strptime(end_time_str, "%I:%M%p")
        time_slots_with_dt.append((start_time, end_time, code))

    # Sort the time slots by start time
    time_slots_with_dt.sort(key=lambda x: x[0])

    # Check for gaps between consecutive time slots
    for i in range(1, len(time_slots_with_dt)):
        prev_end_time = time_slots_with_dt[i - 1][1]
        curr_start_time = time_slots_with_dt[i][0]

        # If there is a gap between the end of one time slot and the start of the next
        if prev_end_time < curr_start_time:
            gap_start_time = prev_end_time
            gap_end_time = curr_start_time
            # Return the gap in the form of a time range (e.g., "2:00pm - 4:00pm")
            gap  = {
                "start_time": gap_start_time.strftime('%I:%M%p').lstrip('0'),
                "end_time": gap_end_time.strftime('%I:%M%p').lstrip('0')
            }
            return gap

    # No gap found, return None
    return None


# def convert_time_to_eventTime_datetime(event, times_to_convert):

#     #NOT USED IN CODE
#     # Convert the ISO 8601 strings to datetime objects
#     event_start_datetime = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))  # Handle UTC
#     event_end_datetime = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))  # Handle UTC
#     print(event_start_datetime)
#     print(event_end_datetime)
#     # Extract the dates from event's start_time and end_time
#     event_start_date = event_start_datetime.date()
#     event_end_date = event_end_datetime.date()

#     print(event_start_date)
#     print(event_end_date)

#     # Initialize a dictionary to store the converted times
#     converted_times = {}

#     for time_label, time_str in times_to_convert.items():
#         # Combine the time with the event's date
#         combined_str = f"{event_start_date} {time_str}"
#         time_as_datetime = datetime.strptime(combined_str, "%Y-%m-%d %I:%M%p")
#         print(combined_str)
#         print(time_as_datetime)
#         # Check if the time crosses over to the next day (e.g., 12:00 AM)
#         if time_label == "end_time" and time_as_datetime.time() < event_start_datetime.time():
#             # Use the next day's date for times past midnight
#             time_as_datetime = time_as_datetime.replace(year=event_end_date.year, 
#                                                         month=event_end_date.month, 
#                                                         day=event_end_date.day)
#             print(combined_str)

#         converted_times[time_label] = time_as_datetime

#     return converted_times


def sort_event_description(event_description):

    '''

    Takes in a string(the event description) and output a string of organized by time

    '''
    # This regular expression matches time periods and their associated check-in codes
    time_pattern = r'(\d{1,2}:\d{2}[APM]+) - (\d{1,2}:\d{2}[APM]+): (\S+)'

    # Find all the time ranges and associated check-in codes in the description
    time_slots = re.findall(time_pattern, event_description)
    print("time_slots to sort: ", time_slots)
    # Convert times to datetime objects
    time_slots_with_dt = []
    for start_time_str, end_time_str, code in time_slots:
        # Parse times using the correct format
        start_time = datetime.strptime(start_time_str, "%I:%M%p")
        end_time = datetime.strptime(end_time_str, "%I:%M%p")
        time_slots_with_dt.append((start_time, end_time, code))

    print("time_slots_with_dt", time_slots_with_dt)
    # Sort the time slots by start time
    time_slots_with_dt.sort(key=lambda x: x[0])

    # Rebuild the event description with the sorted time slots
    sorted_description = ""
    for start_time, end_time, code in time_slots_with_dt:
        start_time_str = start_time.strftime("%I:%M%p").lstrip('0')  # Remove leading zero
        end_time_str = end_time.strftime("%I:%M%p").lstrip('0')  # Remove leading zero
        sorted_description += f"{start_time_str} - {end_time_str}: {code}\n"

    return sorted_description.strip()  # Remove the trailing newline

def parse_event_times_from_description(event_description):
    print("event_description", event_description)
    # Regular expression to match time ranges in the description
    time_pattern = r"(\d{1,2}:\d{2}[APM]+) - (\d{1,2}:\d{2}[APM]+): (\S+)"

    time_slots = re.findall(time_pattern, event_description)
    print("timeslots: ", time_slots)
    
    time_slots_with_dt = []
    for start_time_str, end_time_str, code in time_slots:
        # Parse times into datetime objects
        start_time = datetime.strptime(start_time_str, "%I:%M%p")
        end_time = datetime.strptime(end_time_str, "%I:%M%p")
        time_slots_with_dt.append({
            "start_time": start_time,
            "end_time": end_time,
            "code": code
        })
    print("time_slots", time_slots_with_dt)
    if not time_slots_with_dt:
        print("no timeslots found")
        return None
    return time_slots_with_dt

def find_largest_continuous_interval(time_slots):
    """
    Finds the largest continuous interval from a list of time slots.

    Args:
        time_slots (list): A list of dictionaries containing "start_time" and "end_time".
                           Each "start_time" and "end_time" is a datetime.time object.

    Returns:
        tuple: A tuple containing the earliest start time and the latest end time
               for the largest continuous interval (datetime.time, datetime.time).
    """
    if not time_slots:
        return None

    # Sort the time slots by start time
    time_slots.sort(key=lambda x: x["start_time"])

    # Initialize variables for tracking the largest continuous interval
    current_start = time_slots[0]["start_time"]
    current_end = time_slots[0]["end_time"]
    largest_start = current_start
    largest_end = current_end
    max_duration = timedelta(0)

    for i in range(1, len(time_slots)):
        next_start = time_slots[i]["start_time"]
        next_end = time_slots[i]["end_time"]

        # Check if the current interval is continuous with the next
        if next_start <= current_end:  # Overlapping or adjacent intervals
            current_end = max(current_end, next_end)  # Extend the current interval
        else:  # Non-continuous interval, finalize the current one
            # Calculate duration of the current interval
            current_interval_duration = (
                datetime.combine(date.today(), current_end.time())
                - datetime.combine(date.today(), current_start.time())
            )

            if current_interval_duration > max_duration:
                max_duration = current_interval_duration
                largest_start = current_start
                largest_end = current_end

            # Start a new interval
            current_start = next_start
            current_end = next_end

    # Final check for the last interval
    final_interval_duration = (
        datetime.combine(date.today(), current_end.time())
        - datetime.combine(date.today(), current_start.time())
    )

    if final_interval_duration > max_duration:
        largest_start = current_start
        largest_end = current_end

    return largest_start, largest_end





description = '''10:00AM - 12:00PM: 83VT
12:00PM - 2:00PM: 83VT
2:00PM - 4:00PM: 83VT
8:00PM - 10:00PM: 83VT
4:00PM - 6:00PM: 83VT
'''
# print(description)
# print(check_description_for_gaps(description))