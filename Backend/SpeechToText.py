# Import required packages
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import mtranslate as mt
import time
from Backend.Config import config
import logging
import speech_recognition as sr
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize logger
logger = logging.getLogger("SpeechToText")

# HTML template for speech recognition web interface
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

try:
    start_time = time.time()
    logger.info("Initializing speech recognition system")
    
    # Set input language in HTML template
    HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = '{config.assistant.input_language}';")
    logger.debug(f"Set recognition language to: {config.assistant.input_language}")

    # Save HTML file
    with open(config.paths.voice_html_path, "w") as f:
        f.write(HtmlCode)
    logger.info(f"Speech recognition HTML template saved to: {config.paths.voice_html_path}")

    current_dir = os.getcwd()
    Link = f"{current_dir}/Data/Voice.html"

    # Configure Chrome options for headless operation
    logger.debug("Configuring Chrome options")
    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--headless=new")

    # Initialize Chrome WebDriver
    logger.info("Initializing Chrome WebDriver")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Speech recognition system initialized successfully - response_time={elapsed_time:.2f}")

except Exception as e:
    logger.error(f"Error during initialization: {e}")
    raise

def set_assistant_status(status: str) -> None:
    """
    Update the assistant's status
    
    Args:
        status (str): New status to set
    """
    try:
        logger.debug(f"Setting assistant status to: {status}")
        with open(config.paths.voice_html_path, 'w') as f:
            f.write(status)
        logger.debug("Assistant status updated successfully")
    except Exception as e:
        logger.error(f"Error setting assistant status: {e}")

def modify_query(text: str) -> str:
    """
    Clean and format the recognized text
    
    Args:
        text (str): Raw recognized text
        
    Returns:
        str: Cleaned and formatted text
    """
    try:
        logger.debug(f"Modifying query: {text}")
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # Convert to lowercase for consistency
        text = text.lower()
        
        # Remove any unnecessary punctuation
        text = text.replace("?", "").replace("!", "").replace(".", "")
        
        logger.debug(f"Modified query: {text}")
        return text
    except Exception as e:
        logger.error(f"Error modifying query: {e}")
        return text

def translate_text(text: str) -> str:
    """
    Translate text if needed based on input language
    
    Args:
        text (str): Text to translate
        
    Returns:
        str: Translated text
    """
    try:
        logger.debug(f"Translating text: {text}")
        # For now, we just return the text as is
        # TODO: Implement actual translation if needed
        return text
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return text

def start_speech_recognition() -> str:
    """
    Start speech recognition and return processed text
    
    Returns:
        str: Processed speech text
    """
    try:
        start_time = time.time()
        logger.info("Starting speech recognition")
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Set assistant status to listening
        set_assistant_status("Listening...")
        
        # Use microphone as source
        with sr.Microphone() as source:
            logger.debug("Adjusting for ambient noise")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            logger.debug("Listening for speech")
            audio = recognizer.listen(source)
            
            logger.debug("Processing speech to text")
            text = recognizer.recognize_google(audio, language=config.assistant.input_language)
            
            # Modify and translate text
            text = modify_query(text)
            text = translate_text(text)
            
            elapsed = time.time() - start_time
            logger.info(f"Speech recognition completed in {elapsed:.2f}s: {text}")
            
            return text
            
    except sr.UnknownValueError:
        logger.warning("Speech not understood")
        return ""
    except sr.RequestError as e:
        logger.error(f"Could not request results from speech recognition service: {e}")
        return ""
    except Exception as e:
        logger.error(f"Error in speech recognition: {e}")
        return ""
    finally:
        set_assistant_status("Ready")

def setup_chrome_driver() -> webdriver.Chrome:
    """
    Set up Chrome WebDriver for interactive testing
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    try:
        logger.debug("Setting up Chrome WebDriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logger.debug("Chrome WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Error setting up Chrome WebDriver: {e}")
        raise

# Interactive testing mode
if __name__ == "__main__":
    logger.info("Starting interactive testing mode")
    
    try:
        while True:
            print("\nPress Enter to start listening (or type 'exit' to quit)...")
            user_input = input()
            
            if user_input.lower() == 'exit':
                break
                
            text = start_speech_recognition()
            if text:
                print(f"\nRecognized Text: {text}")
            else:
                print("\nNo speech detected or error occurred")
                
    except KeyboardInterrupt:
        logger.info("Interactive testing mode terminated by user")
    except Exception as e:
        logger.error(f"Error in interactive testing mode: {e}")
    finally:
        logger.info("Interactive testing mode ended")