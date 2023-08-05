
from telegram.ext import Updater, MessageHandler, Filters
import telegram
import openai
from moviepy.editor import AudioFileClip
from elevenlabslib import *
import torch
from torch import autocast
from diffusers import StableDiffusionPipeline
from flask import send_file
import io
import torchvision.transforms as transforms
from telegram import Update
from telegram.ext import CallbackContext


openai.api_key = "API_KEY"
TELEGRAM_API_TOKEN = "API_KEY"
ELEVENLABS_API_KEY = "API_KEY"

user = ElevenLabsUser(ELEVENLABS_API_KEY)
voice = user.get_voices_by_name("Angelina")[0]

model_id = "stabilityai/stable-diffusion-xl-base-1.0"  # Add your model ID here
device = "cpu"  # Add your device here, typically "cuda" for GPU or "cpu" for CPU
pipe = StableDiffusionPipeline.from_pretrained(model_id)
pipe = pipe.to(device)

# Here you would load the text file into memory
# You might need to adjust this part based on how you want to use the text file
with open('persona.txt', 'r') as file:
    persona = file.read()

# Initialize the memory
memory = []


messages = messages = [
    {"role": "system", "content": persona},
    {"role": "system", "content": "You are as a role of my bestfriend, now lets play the following requirements: 1/ your name is Angelina Jolie you are sarcastic. Lastly Use this conversation history to make your decision."}
]


def text_message(update, context):
    ...
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=memory + messages
    )
    ...
    update.message.reply_text(
        "...")
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
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=response["choices"][0]["message"]["content"].strip())
    # Add the user's message to memory
    memory.append({"role": "user", "content": update.message.text})

    # If the user asks for a picture, generate and send one
    if "picture" in update.message.text:
        prompt = update.message.text.replace("picture", "").strip()
        if prompt == "":
            update.message.reply_text(
                text="Sorry, I need more information to generate a picture. Please provide more details.", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            with torch.cuda.amp.autocast():
                image = pipe(prompt, guidance_scale=8.5)  # remove 'added_cond_kwargs'
                # Convert the generated image to a PIL Image
                pil_image = transforms.ToPILImage()(image).convert("RGBA")

                # Create an in-memory file
                img_io = io.BytesIO()

                # Save image to in-memory file
                pil_image.save(img_io, 'JPEG', quality=70)

                # Set the in-memory file to start
                img_io.seek(0)

                # Send the in-memory file
                context.bot.send_photo(chat_id=update.message.chat.id, photo=img_io)
    else:
        # The rest of your text message handling code goes here...
        pass
    
    # Add your code for handling text messages here...


def voice_message(update, context):
    ...
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=memory + messages
    )
    ...
    update.message.reply_text(
        "...")
    voice_file = context.bot.getFile(update.message.voice.file_id)
    voice_file.download("voice_message.ogg")
    audio_clip = AudioFileClip("voice_message.ogg")
    audio_clip.write_audiofile("voice_message.mp3")
    audio_file = open("voice_message.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file).text
    
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
    
    messages.append({"role": "assistant", "content": response_text})
    memory.append({"role": "user", "content": update.message.voice})

    # The rest of your code here

updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(
    Filters.text & (~Filters.command), text_message))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_message))
updater.start_polling()
updater.idle()
