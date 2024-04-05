# Twitch Unban Request Logs

This Python project is designed to retrieve and log unban requests for specified Twitch channels and sends formatted logs to a Discord webhook for convenient tracking.

At this time, it's best used as a backlog logger as Twitch stores appeals dating back to October 2020.

## Features

* Tracks unban requests with statuses of "pending", "approved", "denied", and "canceled".
* Generates detailed Discord embeds for each unban request, including:
    * Date and time of the request
    * Channel name
    * Moderator (if involved)
    * Offending user and ID
    * Appeal reasoning
    * Resolution notes (if any)
    * Direct link to the appeal on Twitch
* Custom color-coding of embeds based on request status
* Fetches profile picture of the broadcaster for the embed footer.

![image](https://github.com/phoen88/TwitchBAPL_logs/assets/147262097/a20a2f8b-e5a8-44e4-9753-07ae9d474776)


## Setup

1. **Obtain Credentials and Configure `config.json`**
   * Get your Twitch API Client ID and OAuth token (see [https://dev.twitch.tv/docs/authentication](https://dev.twitch.tv/docs/authentication)).
   * Create a Discord webhook (see [https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)). 
   * Replace the placeholders in `config.json` with your credentials and the IDs of the Twitch channels you want to monitor. 

2. **Install Dependencies**
   ```pip3 install -r requirements.txt```

## Usage
1. **Run the script:**
   ```python main.py```

