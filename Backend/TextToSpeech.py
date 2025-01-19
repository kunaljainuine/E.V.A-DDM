# Import required packages
import os
import time
import random
import logging
from pathlib import Path

# Initialize logger
logger = logging.getLogger("TextToSpeech")

# Try importing optional dependencies
try:
    import pygame
    import asyncio
    import edge_tts
    import pyttsx3
except ImportError as e:
    logger.error(f"Failed to import optional dependency: {e}")
    raise

def get_speech_output_path():
    """Get the path for speech output file"""
    data_dir = Path("Data")
    if not data_dir.exists():
        data_dir.mkdir(parents=True)
    return str(data_dir / "speech.mp3")

async def TextToAudioFile(text, voice="en-US-JennyNeural") -> None:
    """
    Convert text to speech and save as an audio file using Edge TTS.
    
    Args:
        text (str): Text to be converted to speech
        voice (str): Voice to use for speech synthesis
    """
    try:
        file_path = get_speech_output_path()
        logger.debug(f"Converting text to speech: {text[:100]}...")  # Log first 100 chars

        # Remove existing audio file if present
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Removed existing audio file: {file_path}")

        # Generate speech using Edge TTS with custom voice settings
        communicate = edge_tts.Communicate(text, voice, pitch='+5Hz', rate='+13%')
        await communicate.save(file_path)
        logger.debug(f"Generated speech saved to: {file_path}")
        
    except Exception as e:
        logger.error(f"Error in TextToAudioFile: {e}")
        raise

def TTS(Text, func=lambda r=None: True):
    """
    Play text-to-speech audio with error handling and cleanup.
    
    Args:
        Text (str): Text to be spoken
        func (callable): Callback function for controlling playback
        
    Returns:
        bool: True if playback was successful
    """
    while True:
        try:
            logger.debug("Starting TTS process")
            
            # Convert text to audio file
            asyncio.run(TextToAudioFile(Text))
            logger.debug("Text converted to audio file")

            # Initialize audio playback
            pygame.mixer.init()
            pygame.mixer.music.load(get_speech_output_path())
            pygame.mixer.music.play()
            logger.debug("Started audio playback")

            # Monitor playback status
            while pygame.mixer.music.get_busy():
                if func() == False:
                    logger.debug("Playback interrupted by callback function")
                    break
                pygame.time.Clock().tick(10)

            logger.debug("Audio playback completed")
            return True

        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return False

        finally:
            try:
                # Cleanup audio resources
                func(False)
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                logger.debug("Audio resources cleaned up")

            except Exception as e:
                logger.error(f"Error in cleanup: {e}")

def TextToSpeech(Text, func=lambda r=None: True):
    """
    Smart text-to-speech conversion with length handling.
    For long text, speaks first two sentences and directs to chat screen.
    
    Args:
        Text (str): Text to be spoken
        func (callable): Callback function for controlling playback
    """
    try:
        logger.info(f"Processing text for speech: {Text[:100]}...")  # Log first 100 chars
        Data = str(Text).split(".")

        # List of responses for directing user to chat screen
        responses = [
            "The rest of the result has been printed to the chat screen, kindly check it out sir.",
            "The rest of the text is now on the chat screen, sir, please check it.",
            "You can see the rest of the text on the chat screen, sir.",
            "The remaining part of the text is now on the chat screen, sir.",
            "Sir, you'll find more text on the chat screen for you to see.",
            "The rest of the answer is now on the chat screen, sir.",
            "Sir, please look at the chat screen, the rest of the answer is there.",
            "You'll find the complete answer on the chat screen, sir.",
            "The next part of the text is on the chat screen, sir.",
            "Sir, please check the chat screen for more information.",
            "There's more text on the chat screen for you, sir.",
            "Sir, take a look at the chat screen for additional text.",
            "You'll find more to read on the chat screen, sir.",
            "Sir, check the chat screen for the rest of the text.",
            "The chat screen has the rest of the text, sir.",
            "There's more to see on the chat screen, sir, please look.",
            "Sir, the chat screen holds the continuation of the text.",
            "You'll find the complete answer on the chat screen, kindly check it out sir.",
            "Please review the chat screen for the rest of the text, sir.",
            "Sir, look at the chat screen for the complete answer."
        ]

        # Handle long text by speaking first two sentences and directing to chat
        if len(Data) > 4 and len(Text) >= 250:
            logger.debug("Text exceeds length limit, truncating and adding redirect message")
            truncated_text = " ".join(Text.split(".")[0:2]) + ". " + random.choice(responses)
            logger.debug(f"Truncated text: {truncated_text}")
            TTS(truncated_text, func)
        else:
            logger.debug("Text within length limit, processing full text")
            TTS(Text, func)
            
    except Exception as e:
        logger.error(f"Error in TextToSpeech: {e}")
        # Attempt to speak a simple error message
        TTS("I apologize, but I encountered an error while processing the text.", func)

def speak(text: str) -> bool:
    """
    Convert text to speech and play it
    
    Args:
        text (str): Text to convert to speech
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        start_time = time.time()
        logger.info(f"Converting text to speech: {text[:50]}...")
        
        # Initialize text-to-speech engine
        engine = pyttsx3.init()
        
        # Set voice properties from system voices
        voices = engine.getProperty('voices')
        if voices:  # Use first available voice
            engine.setProperty('voice', voices[0].id)
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 1.0)  # Volume level
        
        # Save speech to file
        logger.debug("Saving speech to file")
        engine.save_to_file(text, get_speech_output_path())
        engine.runAndWait()
        
        # Initialize pygame for audio playback
        logger.debug("Initializing audio playback")
        pygame.mixer.init()
        pygame.mixer.music.load(get_speech_output_path())
        pygame.mixer.music.play()
        
        # Wait for audio to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        elapsed = time.time() - start_time
        logger.info(f"Text-to-speech completed in {elapsed:.2f}s")
        return True
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        return False
    finally:
        try:
            pygame.mixer.quit()
        except Exception as e:
            logger.error(f"Error cleaning up pygame mixer: {e}")

# Interactive testing mode
if __name__ == "__main__":
    logger.info("Starting interactive testing mode")
    
    try:
        while True:
            text = input("\nEnter text to speak (or 'exit' to quit): ")
            if text.lower() == 'exit':
                break
                
            start_time = time.time()
            success = speak(text)
            elapsed = time.time() - start_time
            
            if success:
                print(f"\nSpeech completed in {elapsed:.2f}s")
            else:
                print("\nError occurred during speech synthesis")
                
    except KeyboardInterrupt:
        logger.info("Interactive testing mode terminated by user")
    except Exception as e:
        logger.error(f"Error in interactive testing mode: {e}")
    finally:
        logger.info("Interactive testing mode ended")