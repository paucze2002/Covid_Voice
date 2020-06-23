# by Paulina Czempiel

# modules
import json
import requests
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

# parsehub API
API_KEY = "tuyTdoZ-EpcM"
PROJECT_TOKEN = "ts6oRgtf3ake"
RUN_TOKEN = "tf-4AyrwHqUH"


# TODO: Wrong input check.
# class to read data from parsehub api
class Data:
    # class initialization
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }
        self.data = self.get_data()

    # getting the data from parsehub api
    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data',
                                params={"api_key": API_KEY})
        data = json.loads(response.text)
        return data

    # getting total cases
    def get_total_cases(self):
        data = self.data['total']
        for content in data:
            if content['name'] == 'Coronavirus Cases:':
                return content['value']
        return '0'

    # getting total deaths
    def get_total_deaths(self):
        data = self.data['total']
        for content in data:
            if content['name'] == 'Deaths:':
                return content['value']
        return '0'

    # getting data to country specify by user
    def get_country_data(self, country):
        data = self.data['country']
        for content in data:
            if content['name'].lower() == country.lower():
                return content
        return '0'

    # getting list of countries
    def get_list_of_countries(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())
        return countries

    # updating data from parsehub (thread to still interact with program)
    def update_data(self):
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/run', params=self.params)
        def poll():
            # give access to main thread (voice assistant)
            time.sleep(0.1)
            old_data = self.data
            # every 5s ping url
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    # set new data
                    self.data = new_data
                    print("Data updated!")
                    break
                time.sleep(5)
        t = threading.Thread(target=poll)
        t.start()


# func to say to user
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# func to get audio from user
def get_audio():
    r = sr.Recognizer()
    with sr.Microphone(device_index=0) as source:
        audio = r.listen(source)
        said = ''
        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print('Exception', str(e))
    return said.lower()


# main func to listen to user
def main():
    # initialize data (parsehub api)
    data = Data(API_KEY, PROJECT_TOKEN)
    print('Program started')
    END_PHRASE = 'exit'
    country_list = data.get_list_of_countries()
    # total pattern possible phrase from user
    TOTAL_PATTERNS = {
        re.compile('[\w\s]+ total [\w\s]+ cases'):data.get_total_cases,
        re.compile('[\w\s]+ total cases'): data.get_total_cases,
        re.compile('[\w\s]+ total [\w\s]+ deaths'): data.get_total_deaths,
        re.compile('[\w\s]+ total deaths'): data.get_total_deaths
    }
    # country total possible phrase from user
    COUNTRY_PATTERNS = {
        re.compile('[\w\s]+ cases [\w\s]+'): lambda country: data.get_country_data(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths']
    }
    # update command
    UPDATE_COMMAND = 'update'
    # listen to user and check pattern
    while True:
        print('Listening...')
        text = get_audio()
        print(text)
        result = None
        # looking for country from user input in list of countries and run func from pattern
        for pattern, func in COUNTRY_PATTERNS.items():
            if pattern.match(text):
                words = set(text.split(' '))
                for country in country_list:
                    if country in words:
                        result = func(country)
                        break
        # looking for func in total patterns and run it
        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(text):
                result = func()
                break
        # updating data
        if text == UPDATE_COMMAND:
            result = "Data is being updated. This may take a moment."
            data.update_data()
        if result:
            speak(result)
        # stop listen
        if text.find(END_PHRASE) != -1:
            print('Exiting the program...')
            break


main()