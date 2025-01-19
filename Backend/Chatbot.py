# Import required packages
from groq import Groq
import datetime
import logging
from Backend.Config import config

# Initialize logger
logger = logging.getLogger("Chatbot")

# Initialize Groq client
try:
    client = Groq(api_key=config.api.groq_api_key)
    logger.info("Groq client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}")
    raise

# Initialize messages list for chat history
messages = config.load_chat_log()

# Define system prompt for the chatbot
System = f"""Hello, I am {config.assistant.username}, You are a very accurate and advanced chatbot named {config.assistant.assistant_name} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

# Initialize system message for the chatbot
SystemChatBot = [
    {"role": "system", "content": System},
]

def RealtimeInformation():
    """
    Get current date and time information formatted for the chatbot.
    
    Returns:
        str: Formatted string containing current date and time information
    """
    try:
        current_date_time = datetime.datetime.now()
        day = current_date_time.strftime("%A")
        date = current_date_time.strftime("%d")
        month = current_date_time.strftime("%B")
        year = current_date_time.strftime("%Y")
        hour = current_date_time.strftime("%H")
        minute = current_date_time.strftime("%M")
        second = current_date_time.strftime("%S")

        data = f"Please use this real-time information if needed,\n"
        data += f"Day: {day}\n Date: {date}\n Month: {month}\n Year: {year}\n"
        data += f"Time: {hour} hours :{minute} minutes :{second} seconds.\n"
        
        logger.debug("Generated realtime information")
        return data
    except Exception as e:
        logger.error(f"Error generating realtime information: {e}")
        return ""

def AnswerModifier(Answer):
    """
    Remove empty lines from the chatbot's response.
    
    Args:
        Answer (str): Raw response from the chatbot
        
    Returns:
        str: Cleaned response with empty lines removed
    """
    try:
        lines = Answer.split('\n')
        not_empty_lines = [line for line in lines if line.strip()]
        modified_answer = '\n'.join(not_empty_lines)
        logger.debug("Modified answer by removing empty lines")
        return modified_answer
    except Exception as e:
        logger.error(f"Error modifying answer: {e}")
        return Answer

def ChatBot(Query):
    """
    Process user query through the Groq LLM and return the response.
    
    Args:
        Query (str): User's input query
        
    Returns:
        str: AI's response to the query
    """
    try:
        logger.info(f"Processing query: {Query}")
        
        # Load existing chat history
        messages = config.load_chat_log()

        # Add user's query to messages
        messages.append({"role": "user", "content": f"{Query}"})
        logger.debug("Added user query to messages")

        # Generate response using Groq
        logger.debug("Generating response using Groq")
        completion = client.chat.completions.create(
            model=config.models.groq_chat_model,
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        # Collect response from stream
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        # Clean up response
        Answer = Answer.replace("</s>", "")
        logger.debug("Collected and cleaned response from stream")

        # Add assistant's response to messages
        messages.append({"role": "assistant", "content": Answer})
        logger.debug("Added assistant response to messages")

        # Save updated chat history
        config.save_chat_log(messages)

        logger.info("Successfully processed query and generated response")
        return AnswerModifier(Answer=Answer)
    
    except Exception as e:
        logger.error(f"Error in ChatBot: {e}")
        # Reset chat history on error
        config.save_chat_log([])
        return ChatBot(Query)
    
if __name__ == "__main__":
    # Interactive testing mode
    logger.info("Starting interactive testing mode")
    while True:
        user_input = input("Enter your Question: ")
        print(ChatBot(user_input))