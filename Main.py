# Import required modules and packages
from Frontend.GUI import (
    GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen, TempDirectoryPath,
    SetMicrophoneStatus, AnswerModifier, QueryModifier, GetMicrophoneStatus, GetAssistantStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import start_speech_recognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.Config import config
import asyncio
from time import sleep
import subprocess
import threading
import json
import os
import logging

# Initialize logger
logger = logging.getLogger("Main")

# List of supported functions
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# Global list for subprocesses
subprocesses = []

# Initialize chat with default message if no chat history exists
def ShowDefaultChatIfNoChats():
    try:
        chat_log = config.load_chat_log()
        if not chat_log:
            logger.debug("No chat history found, showing default message")
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                file.write("")
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write(config.assistant.default_message)
    except Exception as e:
        logger.error(f"Error showing default chat: {e}")

# Format and integrate chat history
def ChatLogIntegration():
    try:
        json_data = config.load_chat_log()
        formatted_chatlog = ""
        for entry in json_data:
            if entry["role"] == "user":
                formatted_chatlog += f"{config.assistant.username}: {entry['content']}\n"
            elif entry["role"] == "assistant":
                formatted_chatlog += f"{config.assistant.assistant_name}: {entry['content']}\n"

        logger.debug("Writing formatted chat log to database file")
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatlog))
    except Exception as e:
        logger.error(f"Error integrating chat log: {e}")

# Display chat history in GUI
def ShowChatsOnGUI():
    try:
        with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as file:
            data = file.read()
            if data:
                lines = data.split('\n')
                result = '\n'.join(lines)
                with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as response_file:
                    response_file.write(result)
                logger.debug("Updated GUI with chat history")
    except Exception as e:
        logger.error(f"Error showing chats on GUI: {e}")

# Initialize application state
def InitialExecution():
    try:
        logger.info("Starting initial execution")
        SetMicrophoneStatus("False")
        ShowTextToScreen("")
        ShowDefaultChatIfNoChats()
        ChatLogIntegration()
        ShowChatsOnGUI()
        logger.info("Initial execution completed")
    except Exception as e:
        logger.error(f"Error in initial execution: {e}")

# Main execution loop handling user interactions
async def MainExecution():
    try:
        task_execution = False
        image_execution = False
        image_generation_query = ""

        # Start listening for user input
        SetAssistantStatus("Listening...")
        query = start_speech_recognition()
        if not query:
            logger.warning("No speech detected")
            return False

        ShowTextToScreen(f"{config.assistant.username}: {query}")
        SetAssistantStatus("Thinking...")
        decision = FirstLayerDMM(query)

        logger.info(f"Decision: {decision}")

        # Process decision types
        general_queries = [i for i in decision if i.startswith("general")]
        realtime_queries = [i for i in decision if i.startswith("realtime")]
        is_general = bool(general_queries)
        is_realtime = bool(realtime_queries)

        merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in decision if i.startswith("general") or i.startswith("realtime")]
        )

        # Handle image generation requests
        for queries in decision:
            if "generate " in queries:
                image_generation_query = str(queries)
                image_execution = True

        # Handle automation tasks
        for queries in decision:
            if not task_execution and any(queries.startswith(func) for func in Functions):
                await Automation(list(decision))
                task_execution = True

        # Process image generation
        if image_execution:
            logger.info(f"Starting image generation: {image_generation_query}")
            with open(config.paths.image_gen_status_path, "w") as file:
                file.write(f"{image_generation_query}, True")
            try:
                p1 = subprocess.Popen(['python', 'Backend/ImageGeneration.py'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE, shell=False)
                subprocesses.append(p1)
            except Exception as e:
                logger.error(f"Error starting ImageGeneration.py: {e}")

        # Handle realtime and general queries
        if (is_general and is_realtime) or is_realtime:
            SetAssistantStatus("Searching...")
            answer = RealtimeSearchEngine(QueryModifier(merged_query))
            ShowTextToScreen("Answering...")
            TextToSpeech(answer)
            return True

        # Handle individual query types
        for query in decision:
            if "general" in query:
                SetAssistantStatus("Thinking...")
                query_final = query.replace("general ", "")
                answer = ChatBot(QueryModifier(query_final))
                ShowTextToScreen(f"{config.assistant.assistant_name}: {answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(answer)
                return True
                
            elif "realtime" in query:
                SetAssistantStatus("Searching...")
                query_final = query.replace("realtime ", "")
                answer = RealtimeSearchEngine(QueryModifier(query_final))
                ShowTextToScreen(f"{config.assistant.assistant_name}: {answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(answer)
                return True
                
            elif "exit" in query:
                query_final = "Okay, Bye!"
                answer = ChatBot(QueryModifier(query_final))
                ShowTextToScreen(f"{config.assistant.assistant_name}: {answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(answer)
                os._exit(1)

        return False

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        return False

# Thread for handling voice commands and AI responses
def FirstThread():
    logger.info("Starting voice command thread")
    while True:
        try:
            current_status = GetMicrophoneStatus()
            if current_status == "True":
                asyncio.run(MainExecution())
            else:
                ai_status = GetAssistantStatus()
                if "Available..." in ai_status:
                    sleep(0.1)
                else:
                    SetAssistantStatus("Available...")
        except Exception as e:
            logger.error(f"Error in voice command thread: {e}")
            sleep(1)  # Prevent rapid retries on error

# Thread for GUI
def SecondThread():
    logger.info("Starting GUI thread")
    try:
        GraphicalUserInterface()
    except Exception as e:
        logger.error(f"Error in GUI thread: {e}")

# Cleanup function
def cleanup():
    logger.info("Cleaning up resources")
    try:
        for process in subprocesses:
            process.terminate()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Main entry point
if __name__ == "__main__":
    try:
        logger.info("Starting EVA DDM")
        InitialExecution()
        
        # Start threads
        voice_thread = threading.Thread(target=FirstThread, daemon=True)
        voice_thread.start()
        
        # Start GUI (this will block until GUI closes)
        SecondThread()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        cleanup()
        logger.info("Application shutdown complete")