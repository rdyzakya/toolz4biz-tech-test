from quart import Quart, request
from googlesearch import search
import os
import aiohttp
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from pydub import AudioSegment
from twilio.twiml.voice_response import VoiceResponse
import asyncio
from src import asr, scrape
from melo.api import TTS

# app = Quart(__name__)
app = Quart(__name__, static_folder='received_audio')


# Twilio credentials (make sure these are securely stored and not hard-coded in production)
with open("./whatsapp_config", 'r') as fp:
    whatsapp_config = fp.readlines()
TWILIO_ACCOUNT_SID = whatsapp_config[0].split("=")[1]
TWILIO_AUTH_TOKEN = whatsapp_config[1].split("=")[1]
TWILIO_PHONE_NUMBER = whatsapp_config[2].split("=")[1]

# Directory to save received audio files
AUDIO_DIR = "./received_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Define states for conversation
WAITING_FOR_FIRST_AUDIO, WAITING_FOR_SECOND_AUDIO = range(2)
user_state = {}
audio_files = {}

@app.route('/processed_audio/<filename>')
async def processed_audio(filename):
    return await app.send_static_file(filename)

@app.route("/", methods=["POST"])
async def bot():
    form_data = await request.form
    from_number = form_data.get('From', '') #.replace(":+",'')
    user_msg = form_data.get('Body', '').lower()
    num_media = int(form_data.get('NumMedia', 0))

    response = MessagingResponse()

    # Initialize state for new users
    if from_number not in user_state:
        user_state[from_number] = None
        audio_files[from_number] = []

    # Check if user is in the process of sending audio files
    if user_state[from_number] in [WAITING_FOR_FIRST_AUDIO, WAITING_FOR_SECOND_AUDIO] and num_media > 0:
        media_url = form_data.get('MediaUrl0', '')
        media_format = form_data.get('MediaContentType0', '').split('/')[-1]
        audio_path = os.path.join(AUDIO_DIR, f"{from_number.replace(':+','')}_{len(audio_files[from_number]) + 1}.{media_format}")

        # Download the audio file with authentication
        async with aiohttp.ClientSession() as session:
            async with session.get(media_url, auth=aiohttp.BasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)) as resp:
                media_data = await resp.read()

        with open(audio_path, 'wb') as f:
            f.write(media_data)

        audio_files[from_number].append(audio_path)

        if user_state[from_number] == WAITING_FOR_FIRST_AUDIO:
            response.message('First audio received. Please send the second audio file.')
            user_state[from_number] = WAITING_FOR_SECOND_AUDIO
        elif user_state[from_number] == WAITING_FOR_SECOND_AUDIO:
            response.message('Second audio received. Processing...')
            user_state[from_number] = None

            # Process the audio files asynchronously
            asyncio.create_task(process_and_respond(from_number, audio_files[from_number]))
            audio_files[from_number] = []

    elif user_msg == 'special_command':
        response.message('Please send the first audio file.')
        user_state[from_number] = WAITING_FOR_FIRST_AUDIO
    else:
        q = user_msg + " geeksforgeeks.org"
        search_results = [result for result in search(q, num_results=3)]
        msg = response.message(f"--- Results for '{user_msg}' ---")
        for result in search_results:
            msg.body(result)

    return str(response)

async def process_and_respond(from_number, audio_paths):
    result_audio_path = await process_audio_files(audio_paths[0], audio_paths[1])
    await send_processed_audio(from_number, result_audio_path)

async def process_audio_files(first_audio_path: str, second_audio_path: str) -> str:
    # Example processing logic: Combine the two audio files into one
    origin = asr.run_asr_local(first_audio_path)
    destination = asr.run_asr_local(second_audio_path)

    print("origin :", origin)
    print("destination :", destination)

    direction_speech = scrape.get_direction_speech(origin, destination, headless=True)

    # Speed is adjustable
    speed = 0.8

    # CPU is sufficient for real-time inference.
    # You can set it manually to 'cpu' or 'cuda' or 'cuda:0' or 'mps'
    device = 'auto' # Will automatically use GPU if available

    # English 
    model = TTS(language='EN', device=device)
    speaker_ids = model.hps.data.spk2id

    # American accent
    mp3_path = os.path.join(AUDIO_DIR, 'result_audio.mp3')
    model.tts_to_file(direction_speech.replace('\n', " ,\n"), speaker_ids['EN-US'], mp3_path, speed=speed)

    # ogg_path = os.path.join(AUDIO_DIR, 'result_audio.ogg')

    # audio = AudioSegment.from_mp3(mp3_path)
    # audio.export(ogg_path, format='ogg')

    # return ogg_path
    return mp3_path

async def send_processed_audio(to_number, audio_path):
    # Construct the URL for the audio file
    audio_url = request.url_root + audio_path[2:]
    audio_url = audio_url.replace('\\','/')

    # Send the processed audio file back to the user
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body="Here is your processed audio file.",
        # from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
        from_=f'whatsapp:+14155238886',
        to=to_number,
        media_url=[audio_url]
    )
    print(f"Sent message: {message.sid}")

if __name__ == "__main__":
    app.run()
