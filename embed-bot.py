import re
import os
import discord
from dotenv import load_dotenv
from unalix import clear_url, unshort_url

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

short_urls = ['youtu.be', 'bit.ly', 'tiny.cc', 't.co','g.co','tinyurl.com','t.me','x.co']
base_urls = ['www.facebook.com', 'www.instagram.com', 'twitter.com', 'x.com']
replacement_urls = {'www.facebook.com':'facebed.com', 'www.instagram.com':'www.kkinstagram.com', 'x.com':'nitter.net', 'twitter.com':'nitter.net'}

def embed_url(url):
    url_to_replace = base_urls[base_urls.index(strip_url(url))]
    return url.replace(url_to_replace, replacement_urls[url_to_replace])

def strip_url(url):
    return url[8:url.find("/", 8)]

@client.event
async def on_message(message):
    permissions = message.channel.permissions_for(message.guild.me)
    if message.author == client.user:
        # Suppress embeds for bot messages if unable to suppress embeds for original message to avoid visual clutter
        if not permissions.manage_messages:
            await message.edit(suppress=True)
        # Add :wastebasket: emoji for easy deletion if necessary
        if permissions.add_reactions and permissions.read_message_history and permissions.manage_messages:
            await message.add_reaction('🗑')
    # Though this else is not necessary since the bot should never send
    # links with tracking parameters, include it anyways to be safe
    # against infinite recursion
    else:
        # Extract links and clean
        urls = re.findall('(?P<url>https?://[^s]+)', message.content)
        cleaned = []
        for url in urls:
            # Ignore trailing & in comparing, as these are not used for tracking
            # This is to fix a bug where right clicking on an image in the Discord *app* (not browser) 
            # > Copy Link on context menu would create a link ending in &
            # Pasting this link into Discord would then trigger the bot since the cleaned link removed the &, 
            # even though the image link didn't have tracking parameters
            print("[DEBUG]Processing url: " + url)
            if strip_url(url) in short_urls and strip_url(unshort_url(url)) in base_urls:
                cleaned.append(embed_url(unshort_url(url)))
            elif strip_url(url) in short_urls:
                cleaned.append(unshort_url(url))
            elif clear_url(url).strip('&') != url.strip('&') and strip_url(url) in base_urls:
                cleaned.append(embed_url(clear_url(url)))
            elif strip_url(url) in base_urls:
                cleaned.append(embed_url(url))
            elif clear_url(url).strip('&') != url.strip('&'):
                cleaned.append(clear_url(url))

        # Send message and add reactions
        if cleaned:
            print("[DEBUG]Processed urls: " + " ".join(map(str, cleaned)))
            # Suppress embeds for original message to avoid visual clutter
            if permissions.manage_messages:
                await message.edit(suppress=True)
            text = 'Changing url to one that can embed in discord or one that doesn\'t have tracking or both! :\n' + '\n'.join(cleaned)
            await message.reply(text, mention_author=False)
            
@client.event
async def on_raw_reaction_add(payload):
    # Delete messages if the original sender clicks the trash can react
    if payload.emoji.name != '🗑':
        return

    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if message.reference is None or message.author != client.user:
        return

    original_channel = await client.fetch_channel(message.reference.channel_id)
    original_message = await original_channel.fetch_message(message.reference.message_id)
    user = await client.fetch_user(payload.user_id)
    permissions = message.channel.permissions_for(message.guild.me)

    if permissions.manage_messages and original_message.author == user:
        await message.delete()
        #deleted_messages.inc()
    
if __name__ == '__main__':
    #start_http_server(8000)
    load_dotenv()
    client.run(os.environ['TOKEN'])
