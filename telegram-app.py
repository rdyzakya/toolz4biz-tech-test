import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes
from telegram.ext import filters
import os
from src import asr, scrape
from melo.api import TTS

with open("telegram_api_token", 'r') as fp:
    TOKEN = fp.read()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define states for the conversation
WAITING_FOR_FIRST_AUDIO, WAITING_FOR_SECOND_AUDIO = range(2)

# Directory to save received audio files
AUDIO_DIR = "./received_audio"

# Ensure the directory exists
os.makedirs(AUDIO_DIR, exist_ok=True)

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hi! I am your bot. Use /help to see available commands.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Available commands:\n/start - Start the bot\n/help - Show help\n/special_command - Process two audio files')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

async def special_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Please send the first audio file.')
    return WAITING_FOR_FIRST_AUDIO

async def receive_first_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.voice:
        audio_file = await update.message.voice.get_file()
        await audio_file.download_to_drive(os.path.join(AUDIO_DIR, 'first_audio.ogg'))
        await update.message.reply_text('First audio received. Please send the second audio file.')
        return WAITING_FOR_SECOND_AUDIO
    else:
        await update.message.reply_text('Please send a valid audio file.')
        return WAITING_FOR_FIRST_AUDIO

async def receive_second_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.voice:
        audio_file = await update.message.voice.get_file()
        await audio_file.download_to_drive(os.path.join(AUDIO_DIR, 'second_audio.ogg'))
        await update.message.reply_text('Second audio received. Processing...')
        
        # Process the audio files (define your own processing logic)
        result_audio_path = process_audio_files(
            os.path.join(AUDIO_DIR, 'first_audio.ogg'),
            os.path.join(AUDIO_DIR, 'second_audio.ogg')
        )

        # Send the processed audio file back to the user
        with open(result_audio_path, 'rb') as audio:
            await update.message.reply_audio(audio=audio)

        # End the conversation
        return ConversationHandler.END
    else:
        await update.message.reply_text('Please send a valid audio file.')
        return WAITING_FOR_SECOND_AUDIO

def process_audio_files(first_audio_path: str, second_audio_path: str) -> str:
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

    from pydub import AudioSegment

    ogg_path = os.path.join(AUDIO_DIR, 'result_audio.ogg')

    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(ogg_path, format='ogg')

    return ogg_path

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    # Replace 'YOUR_TOKEN_HERE' with your bot's API token
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler for special_command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('special_command', special_command)],
        states={
            WAITING_FOR_FIRST_AUDIO: [MessageHandler(filters.VOICE, receive_first_audio)],
            WAITING_FOR_SECOND_AUDIO: [MessageHandler(filters.VOICE, receive_second_audio)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(conv_handler)

    # Log all errors
    application.add_error_handler(error)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
