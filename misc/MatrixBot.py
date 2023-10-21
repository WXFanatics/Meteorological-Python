#!/usr/bin/env python3

import time
import re
import html
import feedparser
from matrix_client.client import MatrixClient

# Matrix room ID where the alerts will be posted
ROOM_ID = "YourRoomIDHere"
# URL of the weather alerts RSS feed - Find here: https://mesonet.agron.iastate.edu/projects/iembot/
RSS_FEED_URL = "https://mesonet.agron.iastate.edu/iembot-rss/room/taechat.xml"
# File to store the URLs of processed messages
PROCESSED_MESSAGES_FILE = "processed_messages.txt"

# Keywords to exclude
EXCLUDED_KEYWORDS = ["Climate Report", "Zone Forecast Package", "Terminal Aerodrome Forecast", "CWA", "Rip Currents Statement", "Marine Weather Statement"]  # Add more keywords as needed
#EXCLUDED_KEYWORDS = ["Climate Report", "Zone Forecast Package", "Terminal Aerodrome Forecast", "CWA", "Area Forecast Discussion", "Short Range Forecast Discussion", "Special Weather Statement", "Hazardous Weather Outlook", "Rip Currents Statement", "Flood Advisory", "Frost Advisory", "Marine Weather Statement"]  # Add more keywords as needed

# Maximum length of the message to be posted (in characters)
MAX_MESSAGE_LENGTH = 8000  # Adjust the value as needed

def load_processed_messages():
    try:
        with open(PROCESSED_MESSAGES_FILE, "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

def save_processed_messages(processed_messages):
    with open(PROCESSED_MESSAGES_FILE, "w") as file:
        file.write("\n".join(processed_messages))

def truncate_message(message, max_length):
    if len(message) > max_length:
        return message[:max_length-3] + "..."
    return message

def extract_alert_info(summary):
    # Remove HTML tags from the summary
    cleaned_summary = re.sub(r"<.*?>", "", summary)

    # Remove the unwanted sections (LAT, LON, TIME, MOT, LOC) and random numbers
    cleaned_summary = re.sub(r"(LAT|LON|TIME|MOT|LOC)[^:]*:.*?\n", "", cleaned_summary, flags=re.IGNORECASE)
    cleaned_summary = re.sub(r"\d+\s", "", cleaned_summary)

    return cleaned_summary.strip()

def post_weather_alerts():
    # Connect to the Matrix server
    client = MatrixClient("https://matrix.org") #Replace with your Matrix Host/Server
    client.login("YourMatrixUsername", "YourMatrixPassword")  # Replace with your Matrix account details

    # Join the desired Matrix room
    room = client.join_room(ROOM_ID)

    # Load the set of processed message URLs
    processed_messages = load_processed_messages()

    while True:
        # Fetch and parse the RSS feed
        feed = feedparser.parse(RSS_FEED_URL)

        # Reverse the order of entries to process the newest alert last
        reversed_entries = reversed(feed.entries)

        # Iterate over the reversed feed entries and post the new alerts to the Matrix room
        for entry in reversed_entries:
            entry_link = entry.link

            # Check if the message has already been processed
            if entry_link in processed_messages:
                continue  # Skip the already processed message

            title = entry.title
            summary = entry.summary

            # Exclude the <link> section from the summary
            summary = re.sub(r"<link>.*?</link>", "", summary)

            # Check if the message contains any excluded keywords
            if any(keyword in title or keyword in summary for keyword in EXCLUDED_KEYWORDS):
                continue  # Skip the message

            # Extract relevant information from the summary
            alert_info = extract_alert_info(summary)

            # Compose the message to be posted in the Matrix room
            message = f"**Weather Alert:**\n\n{title}\n\n{alert_info}"
            message = truncate_message(message, MAX_MESSAGE_LENGTH)

            # Send the message to the Matrix room
            room.send_text(message)

            # Add the message URL to the set of processed messages
            processed_messages.add(entry_link)

        # Save the updated set of processed message URLs
        save_processed_messages(processed_messages)

        # Wait for a delay before checking for new messages again
        time.sleep(300)  # Wait for 5 minutes

    # Disconnect from the Matrix server
    client.logout()

# Run the bot to post weather alerts
post_weather_alerts()
