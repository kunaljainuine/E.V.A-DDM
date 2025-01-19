# Import required packages
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os

# Load environment variables
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Initialize messages list for chat history
messages = []

# Define system context for content generation
SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ['Username']}, You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems, shayri etc."}]

# CSS classes for web scraping
classes = ["zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", 
           "tw-Data-text tw-text-small tw-ta", "IZ6rdc", "O5uR6d LTKOO", "vlzY6d", 
           "webanswers-webanswers_table__webanswers-table", "dDoNo ikb4Bb gsrt", "sXLaOe", 
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

# User agent for web requests
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"

# Professional response templates
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need-don't hesitate to ask."
]

def GoogleSearch(Topic):
    """
    Open a Google search in the default browser.
    
    Args:
        Topic (str): Search query
        
    Returns:
        bool: True if search was successful
    """
    search(Topic)
    return True

def Content(Topic):
    """
    Generate and save content using AI, then open it in notepad.
    
    Args:
        Topic (str): Content topic/prompt
        
    Returns:
        bool: True if content was generated and opened successfully
    """
    def OpenNotepad(File):
        """Open a file in the default text editor."""
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])

    def ContentWriterAI(prompt):
        """Generate content using Groq AI model."""
        messages.append({"role": "user", "content": f"{prompt}"})

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer

    Topic = Topic.replace("Content ", "")
    ContentByAI = ContentWriterAI(Topic)

    # Save generated content to file
    with open(rf"Data/{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI)
        file.close()

    OpenNotepad(rf"Data/{Topic.lower().replace(' ', '')}.txt")
    return True

def YoutubeSearch(Topic):
    """
    Open YouTube search results in browser.
    
    Args:
        Topic (str): Search query
        
    Returns:
        bool: True if search was opened successfully
    """
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYoutube(query):
    """
    Play a YouTube video based on search query.
    
    Args:
        query (str): Search query
        
    Returns:
        bool: True if video started playing
    """
    playonyt(query)
    return True

def OpenApp(app, sess=requests.session()):
    """
    Open an application or its website if app not found locally.
    
    Args:
        app (str): Application name
        sess (requests.Session): Session for web requests
        
    Returns:
        bool: True if app was opened successfully
    """
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        def extract_links(html):
            """Extract links from Google search results."""
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', {'jsname': 'UWckNb'})
            return [link.get('href') for link in links]

        def search_google(query):
            """Perform Google search and return HTML content."""
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": useragent}
            response = sess.get(url, headers=headers)

            if response.status_code == 200:
                return response.text
            else:
                print("Failed to retrieve search results.")
            return None
        
        html = search_google(app)
        if html:
            link = extract_links(html)[0]
            webopen(link)
        return True

def CloseApp(app):
    """
    Close a running application.
    
    Args:
        app (str): Application name
        
    Returns:
        bool: True if app was closed successfully
    """
    if "chrome" in app:
        pass
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except:
            return False

def System(command):
    """
    Execute system commands for volume control.
    
    Args:
        command (str): System command to execute
        
    Returns:
        bool: True if command was executed successfully
    """
    def mute():
        """Mute system volume."""
        keyboard.press_and_release("volume mute")

    def unmute():
        """Unmute system volume."""
        keyboard.press_and_release("volume mute")

    def volume_up():
        """Increase system volume."""
        keyboard.press_and_release("volume up")

    def volume_down():
        """Decrease system volume."""
        keyboard.press_and_release("volume down")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":    
        volume_up()
    elif command == "volume down":
        volume_down()
    
    return True

async def TranslateAndExecute(commands: list[str]):
    """
    Translate commands into function calls and execute them asynchronously.
    
    Args:
        commands (list[str]): List of command strings
        
    Yields:
        Results of command execution
    """
    funcs = []

    for command in commands:
        if command.startswith("open "):
            if "open it" in command or "open file" == command:
                pass
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
                funcs.append(fun)
        elif command.startswith("general ") or command.startswith("realtime "):
            pass
        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)
        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))
            funcs.append(fun)
        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)
        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)
        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YoutubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)
        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)
        else:
            print(f"No function found for {command}")

    results = await asyncio.gather(*funcs)
    for result in results:
        if isinstance(result, str):
            yield result
        else:
            yield result

async def Automation(commands: list[str]):
    """
    Main automation function that processes a list of commands.
    
    Args:
        commands (list[str]): List of commands to execute
        
    Returns:
        bool: True if all commands were executed successfully
    """
    async for result in TranslateAndExecute(commands):
        pass
    return True