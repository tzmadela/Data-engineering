import os
import requests
import xml.etree.ElementTree as ET
from pydub import AudioSegment
import logging

# Set up logging configuration
logging.basicConfig(filename='podcast_downloader.log', level=logging.ERROR)

def construct_podcast_url(podcast_names):
    base_url = 'https://omny.fm/shows/'
    return f'{base_url}{podcast_names}/playlists/podcast.rss'

def extract_podcast_title(rss_url):
    response = requests.get(rss_url)
    if response.status_code == 200:
        # Parse the XML response
        root = ET.fromstring(response.content)

        # Find the channel element and extract the podcast title
        channel = root.find('channel')
        if channel is not None:
            podcast_title = channel.findtext('title')
            return podcast_title.strip()  # Strip whitespace from the title
        else:
            logging.error(f"Channel element not found in RSS feed: {rss_url}")
            return None
    else:
        logging.error(f"Failed to fetch RSS feed from '{rss_url}'. Status code: {response.status_code}")
        return None

def extract_audio_urls_from_rss(rss_url, max_episodes=None):
    response = requests.get(rss_url)
    if response.status_code == 200:
        # Parse the XML response
        root = ET.fromstring(response.content)
        audio_urls = []

        # Find all <item> elements which represent podcast episodes
        for item in root.findall('.//item'):
            # Find <enclosure> elements which typically contain audio URLs
            enclosure = item.find('enclosure')
            if enclosure is not None:
                audio_url = enclosure.get('url')
                audio_urls.append(audio_url)

                # Stop if reached the maximum number of episodes (if specified)
                if max_episodes and len(audio_urls) >= max_episodes:
                    break

        return audio_urls
    else:
        logging.error(f"Failed to fetch RSS feed from '{rss_url}'. Status code: {response.status_code}")
        return []

def download_and_split_audio_from_rss(rss_feed_slugs, output_folder, max_episodes=None, segment_length_ms=15000):
    for slug in rss_feed_slugs:
        # Construct RSS feed URL for the podcast slug
        rss_url = construct_podcast_url(slug)

        # Get the podcast title
        podcast_title = extract_podcast_title(rss_url)
        if not podcast_title:
            continue

        # Create a folder for the current podcast if it doesn't exist
        podcast_folder = os.path.join(output_folder, podcast_title)
        os.makedirs(podcast_folder, exist_ok=True)

        # Extract audio URLs from the RSS feed
        audio_urls = extract_audio_urls_from_rss(rss_url, max_episodes=max_episodes)

        # Download and split audio files from the extracted URLs
        for index, url in enumerate(audio_urls, start=1):
            try:
                # Send a GET request to download the audio content
                response = requests.get(url, timeout=(30, 60))
 
                # Check if the request was successful
                if response.status_code == 200:
                    # Get the audio content
                    audio_content = response.content

                    # Create a folder for the current episode within the podcast folder
                    episode_folder = os.path.join(podcast_folder, f"Episode_{index}")
                    os.makedirs(episode_folder, exist_ok=True)

                    # Save the audio content to a file in the episode folder
                    output_file = os.path.join(episode_folder, f"{podcast_title}_{index}.mp3")
                    with open(output_file, "wb") as audio_file:
                        audio_file.write(audio_content)
                    print(f"Audio file '{output_file}' downloaded successfully.")

                    # Split the audio into segments of specified length (e.g., 15 seconds)
                    split_audio_segments(output_file, episode_folder, segment_length_ms)

                else:
                    logging.error(f"Failed to download the audio file from '{url}'. Status code: {response.status_code}")

            except Exception as e:
                logging.error(f"Error occurred while processing audio from '{url}': {str(e)}")

def split_audio_segments(audio_file_path, output_folder, segment_length_ms=15000):
    # Load the audio file using pydub
    audio = AudioSegment.from_mp3(audio_file_path)

    # Calculate the number of segments
    num_segments = len(audio) // segment_length_ms

    for i in range(num_segments):
        start_time = i * segment_length_ms
        end_time = (i + 1) * segment_length_ms
        segment = audio[start_time:end_time]

        # Output segment filename
        segment_filename = os.path.join(output_folder, f"Segment_{i+1}.mp3")
        segment.export(segment_filename, format="mp3")

        print(f"Segment {i+1} extracted: {segment_filename}")

if __name__ == "__main__":
    # List of podcast slugs (unique identifiers for each podcast)
    podcast_namess = [
        'jabulujule-9-12',
        'the-encore',
        'a-re-tumi-eng-moena',
        'tshiko',
        'asambe-drive-show'
    ]

    # Output folder for downloaded and segmented audio files
    output_folder = r"/home/zimele/Documents/Botlale_Ai"

    # Download and split audio from RSS feeds corresponding to the specified slugs
    download_and_split_audio_from_rss(podcast_namess, output_folder, max_episodes=None, segment_length_ms=15000)
