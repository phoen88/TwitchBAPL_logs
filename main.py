# @phoenpc | phoenp.cc
# v0.8 - Twitch Unban Request Logs (beta)

# TODO: Scability for bigger channels, ensuring rate limits are met,
# potential usage of executing from a bot?
# atp this is better as a backlog retriever for now rather than realtime.
# realtime ('pending' status), you'd probably want to utilize eventsub.
# preferably AIO into a bot is the better solution.
# json needs 2b re-done.

import disnake
import requests
import json
import time 
import datetime

CONFIG_FILE = "config.json" 

def load_config():
    with open(CONFIG_FILE) as f:
        config = json.load(f)
        return config 

def get_unban_requests(broadcaster_id, moderator_id, status):
    config = load_config()
    bearer_token = config["bearer_token"]
    client_id = config["twitch_credentials"]["client_id"]

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Client-Id": client_id
    }
    base_url = "https://api.twitch.tv/helix/moderation/unban_requests"
    params = {
        "broadcaster_id": broadcaster_id,
        "moderator_id": moderator_id,
        "first": 100,
        "status": status  
    }

    all_unban_requests = []
    while True:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()["data"]
        all_unban_requests.extend(data)
        
        # Pagination handling
        cursor = response.json().get("pagination", {}).get("cursor")
        if not cursor:
            break
        params["after"] = cursor

    return all_unban_requests

def fetch_and_sort_all_requests(broadcaster_id, moderator_id):
    statuses = ["denied", "approved", "canceled", "pending"]  
    all_requests = []

    for status in statuses:
        print(f"Fetching {status} unban requests for broadcaster: {broadcaster_id}")
        requests_for_status = get_unban_requests(broadcaster_id, moderator_id, status)
        all_requests.extend(requests_for_status)

    all_requests_sorted = sorted(all_requests, key=lambda x: x["created_at"])
    return all_requests_sorted


def process_and_log_unban_request(request_data):
    request_id = request_data["id"]
    if request_id in logged_requests:
        return # TODO: backlog storage for when we eventually add polling hourly pending requests.

    embed = disnake.Embed(title="Ban Appeal", color=0x9147FF)
    # DATE TIME EMBED (top)
    created_at_str = request_data["created_at"] 
    created_at_dt = datetime.datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")  
    timestamp = int(created_at_dt.timestamp())  
    discord_timestamp = f"<t:{timestamp}:f>"  
    discord_timestamp2 = f"<t:{timestamp}:R>"  
    embed.description = f"Local Date/Time: {discord_timestamp} ({discord_timestamp2})" 

    # in channel and status
    embed.add_field(name="In Channel:", value=request_data["broadcaster_name"], inline=True) 
    status = request_data["status"]
    if "moderator_name" in request_data:
        moderator_name = request_data["moderator_name"]
        if status == "denied":
            embed.add_field(name="Status:", value=f"{status} by {moderator_name}", inline=True)
        elif status == "approved":
            embed.add_field(name="Status:", value=f"{status} by {moderator_name}", inline=True) 
    else:
        embed.add_field(name="Status:", value=status, inline=True)
    
    if status == "denied":
        embed.color = 0xFF0000  # Red
    elif status == "approved":
        embed.color = 0x00FF00  # Green
    elif status == "canceled":  
        embed.color = 0xFFFFFF  # White (lowkey this could be orange)
    elif status == "pending":
        embed.color = 0xFFA500  # Orange (this could be grey of some sort)

    # User/UID
    offending_user = request_data["user_name"]
    offending_user_id = request_data["user_id"]
    broadcaster_name = request_data["broadcaster_name"]  
    hyperlink = f"https://www.twitch.tv/popout/{broadcaster_name}/viewercard/{offending_user}" 
    embed.add_field(name="Offending User:", value=f"[{offending_user}]({hyperlink}) ({offending_user_id})", inline=True)

    # Reason
    embed.add_field(name="Appeal Reasoning:", value=request_data["text"], inline=False) 
    # Res Text
    if "resolution_text" in request_data and request_data["resolution_text"]: 
        embed.add_field(name="Appeal Closure Notes:", value=request_data["resolution_text"], inline=False)
    else:
        embed.add_field(name="Appeal Closure Notes:", value="None provided", inline=False)

    uuid = request_data["id"]
    url = f"https://www.twitch.tv/moderator/unban-request/{uuid}"
    embed.add_field(name="Ban Appeal URL / Request UUID:", value=f"[{uuid}]({url})", inline=False) 
    # 😎
    broadcaster_id = request_data["broadcaster_id"]
    profile_image_url = get_profile_image(broadcaster_id)

    embed.set_footer(text="Twitch Unban Request Logs | phoenp.cc", icon_url=profile_image_url)

    config = load_config() 
    webhook_url = config["discord_webhook_url"]

    requests.post(webhook_url, json={"embeds": [embed.to_dict()]})
    logged_requests.add(request_id)

def get_profile_image(broadcaster_id):
    config = load_config()
    bearer_token = config["bearer_token"]  
    client_id = config["twitch_credentials"]["client_id"]

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Client-Id": client_id
    }
    url = f"https://api.twitch.tv/helix/users?id={broadcaster_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()["data"] 
    if data: 
        return data[0]["profile_image_url"]
    else:
        return None  
        
def process_and_log_unban_requests(unban_requests): 
    # Send in slow chunks to ensure all 100 results from Twitch API get sent to Discord without hitting a rate limit.
    CHUNK_SIZE = 3
    SECONDS_PER_MINUTE = 60
    DELAY_PER_CHUNK = SECONDS_PER_MINUTE / 20  

    for i in range(0, len(unban_requests), CHUNK_SIZE):
        chunk = unban_requests[i:i + CHUNK_SIZE]
        for request in chunk:
            process_and_log_unban_request(request)  
        time.sleep(DELAY_PER_CHUNK) 

def main():
    config = load_config()
    global logged_requests
    logged_requests = set()

    for broadcaster in config["broadcasters"]:
        broadcaster_id = broadcaster["id"]
        moderator_id = config["moderator_id"] 
        try:
            all_sorted_requests = fetch_and_sort_all_requests(broadcaster_id, moderator_id)
            process_and_log_unban_requests(all_sorted_requests)  # Ensure this function handles requests in the order they're passed
        except Exception as e:
            print(f"An error occurred for broadcaster {broadcaster_id}: {e}") 

def fetch_and_log(broadcaster_id, moderator_id): 
    print(f"Fetching unban requests for broadcaster: {broadcaster_id}")
    try:
        unban_requests = get_unban_requests(broadcaster_id, moderator_id)
        print("Unban requests:", unban_requests)
        # Reverse the unban requests to ensure oldest are processed first
        unban_requests_reversed = list(reversed(unban_requests))
        process_and_log_unban_requests(unban_requests_reversed) 
    except Exception as e:
        print(f"An error occurred for broadcaster {broadcaster_id}: {e}")


if __name__ == "__main__":
    main()
