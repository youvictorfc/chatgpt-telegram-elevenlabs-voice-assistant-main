from telegram.ext import Updater, MessageHandler, Filters
import telegram
import openai
from moviepy.editor import AudioFileClip
from elevenlabslib import *


openai.api_key = "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"
TELEGRAM_API_TOKEN = "6245485548:AAEUauwMMgbBfw4d_AVUCuebm_LW1HJYLeE"
ELEVENLABS_API_KEY = "9ebc5a24de61ec4d94c8510abead6d82"

user = ElevenLabsUser(ELEVENLABS_API_KEY)
# This is a list because multiple voices can have the same namesur
voice = user.get_voices_by_name("Chris")[0]


messages = [{"role": "system", "content": "You are as a role of my bestfirend, now lets play the following requirements: 1/ your name is chris hemsworth from the thor. 2/ you are part of the avengers. you are sarcastic. you love having conversations with best frind orin. Lastly Use this conversation history to make your decision."}]


def text_message(update, context):
    update.message.reply_text(
        "I've received a text message! Please give me a second to respond :)")
    messages.append({"role": "user", "content": update.message.text})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    response_text = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": response_text})
    response_byte_audio = voice.generate_audio_bytes(response_text)
    with open('response_elevenlabs.mp3', 'wb') as f:
        f.write(response_byte_audio)
    context.bot.send_voice(chat_id=update.message.chat.id,
                           voice=open('response_elevenlabs.mp3', 'rb'))
    update.message.reply_text(
        text=f"*[Bot]:* {response_text}", parse_mode=telegram.ParseMode.MARKDOWN)


def voice_message(update, context):
    update.message.reply_text(
        "I've received a voice message! Please give me a second to respond :)")
    voice_file = context.bot.getFile(update.message.voice.file_id)
    voice_file.download("voice_message.ogg")
    audio_clip = AudioFileClip("voice_message.ogg")
    audio_clip.write_audiofile("voice_message.mp3")
    audio_file = open("voice_message.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file).text
    update.message.reply_text(
        text=f"*[You]:* _{transcript}_", parse_mode=telegram.ParseMode.MARKDOWN)
    messages.append({"role": "user", "content": transcript})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    response_text = response["choices"][0]["message"]["content"]
    response_byte_audio = voice.generate_audio_bytes(response_text)
    with open('response_elevenlabs.mp3', 'wb') as f:
        f.write(response_byte_audio)
    context.bot.send_voice(chat_id=update.message.chat.id,
                           voice=open('response_elevenlabs.mp3', 'rb'))
    update.message.reply_text(
        text=f"*[Bot]:* {response_text}", parse_mode=telegram.ParseMode.MARKDOWN)
    messages.append({"role": "assistant", "content": response_text})


updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(
    Filters.text & (~Filters.command), text_message))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_message))
updater.start_polling()
updater.idle()
