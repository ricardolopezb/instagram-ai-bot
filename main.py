import openai
from dotenv import dotenv_values
import requests
import shutil
import urllib.request
import os
from datetime import datetime
import glob
from PIL import Image
from pathlib import Path
from instagrapi import Client
import telebot
from enum import Enum
import time
import threading

# Prompt: Give me a ficticious character prompt for generative art, with a specific style.
# Generate image
# backstory: Give me a brief character backstory about the following description: "[description]".
# Upload to Instagram

config_vars = dotenv_values('.env')

try:
    cookie_del = glob.glob("config/*cookie.json")
    os.remove(cookie_del[0])
except:
    pass

class OpenAi:
    def __init__(self):
        self.model_engine = "text-davinci-003"
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def get_completion_with_prompt(self, prompt):
        character_prompts = openai.Completion.create(
            engine=self.model_engine,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )
        return character_prompts.choices[0].text
    
    def get_character_prompt(self):
        return self.get_completion_with_prompt(os.environ.get("ALTERNATIVE_PROMPT_STYLE"))
        #return self.get_completion_with_prompt(config_vars['CHARACTER_PROMPT'])
        
    def get_character_backstory(self, character_description):
        return self.get_completion_with_prompt(os.environ.get("BACKSTORY_PROMPT") + character_description)
    
    def get_full_prompt_with_details(self):
        prompt = "Write a detailed description of " + self.get_character_backstory(self.get_character_prompt()) + " What does it look like?"
        print("DETAILS ASKED\n", prompt)
        return self.get_completion_with_prompt(prompt)

    def get_image_url(self, prompt):
        response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
        )
        image_url = response['data'][0]['url']
        return image_url


    def download_image(self, filepath, filename, url):
        full_path = filepath + filename + ".jpeg"
        urllib.request.urlretrieve(url, full_path)
        return full_path

class Answer(Enum):
    NOT_ANSWERED = 1
    APPROVED = 2
    REJECTED = 3



def _format_saving_filename(filename):
    return filename.strip()[1:len(filename)-3]

def get_sized_image_path(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    new_image = image.resize((1080, 1080))
    new_image.save("sized_image.jpg")
    phot_path = "sized_image.jpg"
    return Path(phot_path)

def upload_post_to_instagram(description, image_path):
    print("Uploading post to Instagram...")
    sized_image_path = get_sized_image_path(image_path)
    hashtagList = "#AIart #neuralart #machinelearningart #digitalart #artificialintelligence #techart #dataart #proceduralart #generativeart #cyberpunkart"
    cl = Client()
    cl.login(os.environ.get("INSTAGRAM_USER"), os.environ.get("INSTAGRAM_PASSWORD"))
    cl.photo_upload(sized_image_path, description+'\n.\n.\n.\n'+hashtagList)
    print("Posted.")


def save_post_data(post_prompt, backstory, img_url):
    formatted_post_prompt = _format_saving_filename(post_prompt)
    date_to_be_saved = str(datetime.now())
    os.makedirs("posts/" + date_to_be_saved, exist_ok=True)
    f = open("posts/" + date_to_be_saved + "/" + date_to_be_saved+".txt", 'w')
    f.write("Prompt:\n" + formatted_post_prompt + "\n\nBackstory: " + backstory.strip())
    f.close()
    print("Saved!")
    return open_ai.download_image("posts/" + date_to_be_saved+"/", date_to_be_saved, img_url)

open_ai = OpenAi()
bot = telebot.TeleBot(os.environ.get("BOT_TOKEN"))
answer = Answer.NOT_ANSWERED

@bot.message_handler(commands = ['start'])
def send_information(message):
    bot.send_message(message.chat.id, "hello my dude")

@bot.message_handler(commands = ['work'])
def work(message):
    print(message.chat.id)
    bot.send_message(os.environ.get("OUR_CHAT_ID"), "working!")
    generate_post()

@bot.message_handler(commands = ['accept'])
def authorize_post_upload(message):
    global answer
    bot.send_message(os.environ.get("OUR_CHAT_ID"), "Post Approved!")
    print("Post Approved!")
    answer = Answer.APPROVED

@bot.message_handler(commands = ['reject'])
def reject_post_upload(message):
    global answer
    bot.send_message(os.environ.get("OUR_CHAT_ID"), "Post Rejected. Sending another one...")
    print("Post Rejected. Sending another one...")
    answer = Answer.REJECTED

def send_possible_post(image_url, backstory):
    print("Sending post...")
    bot.send_photo(os.environ.get("OUR_CHAT_ID"), image_url)
    bot.send_message(os.environ.get("OUR_CHAT_ID"), backstory)

def generate_post():
    character_prompt = open_ai.get_character_prompt()
    backstory = open_ai.get_character_backstory(character_prompt)
    img_url = open_ai.get_image_url(character_prompt)
    return (character_prompt, backstory, img_url)
    #send_possible_post(img_url, backstory)

def start_script():
    global answer
    print('started!')
    (character_prompt, backstory, img_url) = generate_post()
    send_possible_post(img_url, backstory)
    while(answer == Answer.NOT_ANSWERED):
        pass
    if answer == Answer.APPROVED: 
        image_path = save_post_data(character_prompt, backstory, img_url)
        time.sleep(1)
        upload_post_to_instagram(backstory, image_path)
        answer = Answer.NOT_ANSWERED
        time.sleep(79200)
        start_script()
    else:
        answer = Answer.NOT_ANSWERED
        start_script()


script_working = threading.Thread(target=start_script, args=())

bot_listening = threading.Thread(target=bot.infinity_polling, args=(), daemon=True)

bot_listening.start()
script_working.start()


