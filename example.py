import openai
from dotenv import dotenv_values
import requests
import shutil
import urllib.request
import os
from datetime import datetime
from instapy import InstaPy
from instabot import Bot
import glob
from instagrapi import Client
from instagrapi.types import Usertag

# completion: Give me a ficticious character prompt for generative art, with a specific style.
# Generate image
# backstory: Give me a brief character backstory about the following description: "[description]".
# Upload to Instagram

config_vars = dotenv_values('.env')
cookie_del = glob.glob("config/*cookie.json")
os.remove(cookie_del[0])


class OpenAi:
    def __init__(self):
        self.model_engine = "text-davinci-003"
        openai.api_key = config_vars["OPENAI_API_KEY"]

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
        return self.get_completion_with_prompt(config_vars['ALTERNATIVE_PROMPT_STYLE'])
        #return self.get_completion_with_prompt(config_vars['CHARACTER_PROMPT'])
        
    def get_character_backstory(self, character_description):
        return self.get_completion_with_prompt(config_vars['BACKSTORY_PROMPT'] + character_description)
    
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

    def save_image(self, file_name, url):
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            with open(file_name,'wb') as f:
                shutil.copyfileobj(res.raw, f)
            print('Image sucessfully Downloaded: ',file_name)
        else:
            print('Image Couldn\'t be retrieved')

    def download_image(self, filepath, filename, url):
        full_path = filepath + filename + ".jpeg"
        urllib.request.urlretrieve(url, full_path)
        return full_path

class InstagramUploader:
    def __init__(self):
        self.hashtagList = "#AIart #neuralart #machinelearningart #digitalart #artificialintelligence #techart #dataart #proceduralart #generativeart #cyberpunkart"
    


def _format_saving_filename(filename):
    print("FILENAME: ", repr(filename))
    return filename.strip()[1:len(filename)-3]

def upload_post_to_instagram(description, image_path):
    hashtagList = "#AIart #neuralart #machinelearningart #digitalart #artificialintelligence #techart #dataart #proceduralart #generativeart #cyberpunkart"
    cl = Client()
    user = cl.user_info_by_username("itprosta")
    cl.login(config_vars['INSTAGRAM_USER'], config_vars['INSTAGRAM_PASSWORD'])
    media = cl.photo_upload(
        path=image_path,
        caption=description,
        usertags=[Usertag(user=user, x=0.5, y=0.5)]
    )

    

open_ai = OpenAi()

def save_post_data(post_prompt, backstory, img_url):
    formatted_post_prompt = _format_saving_filename(post_prompt)
    date_to_be_saved = str(datetime.now())
    os.makedirs("posts/" + date_to_be_saved, exist_ok=True)
    f = open("posts/" + date_to_be_saved + "/" + date_to_be_saved+".txt", 'w')
    f.write("Prompt:\n" + formatted_post_prompt + "\n\nBackstory: " + backstory.strip())
    f.close()
    return open_ai.download_image("posts/" + date_to_be_saved+"/", date_to_be_saved, img_url)





char_descr = open_ai.get_character_prompt()
#char_descr = open_ai.get_full_prompt_with_details()
backstory = open_ai.get_character_backstory(char_descr)
img_url = open_ai.get_image_url(char_descr)

print("Character: ", char_descr)
print("\nStory:", backstory)
print("Image: ", img_url);
#open_ai.save_image(char_descr+".jpg", img_url)
#os.makedirs(_format_saving_filename(char_descr), exist_ok=True)
#open_ai.download_image(_format_saving_filename(char_descr)+"/", _format_saving_filename(char_descr), img_url)

image_path = save_post_data(char_descr, backstory, img_url)
upload_post_to_instagram(backstory, image_path)

