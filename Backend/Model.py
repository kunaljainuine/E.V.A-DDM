# Import required packages
import cohere
import json
import time
from rich import print 
from Backend.Config import config
import logging
from typing import List, Dict, Any, Optional
import groq

# Initialize logger
logger = logging.getLogger("Model")

# Define recognized function keywords (using a set for faster lookups)
funcs = {
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder"
}

# Define the preamble that guides the AI model on how to categorize queries
preamble = """
You are a Decision-Making Model that categorizes user queries. You will determine if a query is 'general', 'realtime', or requires a specific action. Do not answer the query, only categorize it.

**General Queries:**
- Respond with 'general (query)' for informational queries that can be answered by a language model without needing real-time data. Examples: 'who was akbar?', 'how can I study more effectively?', 'what is Python?'.
- Use 'general (query)' for incomplete queries or those without specific nouns (e.g., 'who is he?', 'what's his net worth?').
- Classify time/date-related questions as 'general (query)' (e.g., 'what's the time?').

**Realtime Queries:**
- Respond with 'realtime (query)' for queries requiring up-to-date information or external data. Examples: 'who is the Indian prime minister?', 'Facebook's recent updates', 'news about coronavirus'.
- Use 'realtime (query)' for queries about specific individuals or current events (e.g., 'who is Akshay Kumar?', 'what is today's news?').

**Actions:**
- Respond with 'open (application name)' to open applications or websites (e.g., 'open Facebook'). For multiple items: 'open app1, open app2'.
- Respond with 'close (application name)' to close applications (e.g., 'close Notepad'). For multiple items: 'close app1, close app2'.
- Respond with 'play (song name)' to play music (e.g., 'play Afsanay'). For multiple songs: 'play song1, play song2'.
- Respond with 'generate image (prompt)' for image requests (e.g., 'generate image of a lion'). For multiple images: 'generate image prompt1, generate image prompt2'.
- Respond with 'reminder (time/date message)' for setting reminders (e.g., 'reminder 9:00pm 25th june business meeting').
- Respond with 'system (task)' for system commands (mute, volume up, etc.). For multiple tasks: 'system task1, system task2'.
- Respond with 'content (topic)' for content generation requests (applications, code, etc.). For multiple topics: 'content topic1, content topic2'.
- Respond with 'google search (topic)' for Google searches. For multiple topics: 'google search topic1, google search topic2'.
- Respond with 'youtube search (topic)' for YouTube searches. For multiple topics: 'youtube search topic1, youtube search topic2'.

**Multiple Tasks:** If a query involves multiple actions (e.g., 'open Facebook and close WhatsApp'), respond with each action separately (e.g., 'open Facebook, close WhatsApp').

**End Conversation:** Respond with 'exit' if the user wants to end the conversation (e.g., 'bye EVA').

**Unclear Queries:** If the query type is unclear or the action is not listed, respond with 'general (query)'.
"""

# Define example chat history for context
ChatHistory = [
    {"role": "User", "message": "how are you?"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "Do you like pizza?"},
    {"role": "Chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have a dancing performance on 5th aug at 11pm"},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."}
]

def initialize_cohere() -> Optional[cohere.Client]:
    """Initialize Cohere client with API key from config"""
    try:
        start_time = time.time()
        client = cohere.Client(config.api.cohere_api_key)
        elapsed = time.time() - start_time
        logger.info(f"Cohere client initialized successfully in {elapsed:.2f}s")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Cohere client: {e}")
        return None

def FirstLayerDMM(prompt: str = "test") -> List[str]:
    """
    First Layer Decision Making Model that categorizes user queries into different types of actions.
    
    Args:
        prompt (str): The user's input query
        
    Returns:
        List[str]: List of categorized actions based on the user's query
    """
    try:
        start_time = time.time()
        logger.info(f"Processing prompt through FirstLayerDMM: {prompt}")
        
        # Initialize Cohere client
        cohere_client = initialize_cohere()
        if not cohere_client:
            raise Exception("Failed to initialize Cohere client")
        
        # Generate response using Cohere's chat model
        logger.debug("Generating response using Cohere chat model")
        stream = cohere_client.chat_stream(
            model=config.models.cohere_model,
            message=prompt,
            temperature=0.7,
            chat_history=ChatHistory,
            prompt_truncation='OFF',
            connectors=[],
            preamble=preamble
        )

        # Collect response from stream
        response = ""
        for event in stream:
            if event.event_type == "text-generation":
                response += event.text
        logger.debug(f"Raw response from Cohere: {response}")

        # Process and clean the response
        response = response.replace("\n", "")
        response = response.split(",")
        response = [i.strip() for i in response]
        logger.debug(f"Cleaned response: {response}")

        # Filter valid functions
        temp = []
        for task in response:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)
        response = temp
        logger.debug(f"Filtered response: {response}")

        # Recursively call if response contains "(query)"
        if "(query)" in str(response):
            logger.debug("Response contains '(query)', making recursive call")
            newresponse = FirstLayerDMM(prompt=prompt)
            return newresponse
        else:
            elapsed = time.time() - start_time
            logger.info(f"FirstLayerDMM processing completed in {elapsed:.2f}s")
            return response
            
    except Exception as e:
        logger.error(f"Error in FirstLayerDMM: {e}")
        return ["general " + prompt]  # Fallback to general query

def process_prompt(prompt: str, chat_history: List[dict]) -> str:
    """Process user prompt with chat history"""
    try:
        logger.info(f"Processing prompt: {prompt}")
        start_time = time.time()
        formatted_history = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in chat_history[-5:]  # Last 5 messages for context
        ])
        processed_prompt = f"{formatted_history}\nHuman: {prompt}\nAssistant:"
        elapsed_time = time.time() - start_time
        logger.debug(f"Prompt processed in {elapsed_time:.2f}s")
        return processed_prompt
    except Exception as e:
        logger.error(f"Error processing prompt: {e}", exc_info=True)
        return prompt

def add_to_chat_history(role: str, content: str, chat_history: List[dict]) -> List[dict]:
    """Add message to chat history and save"""
    try:
        logger.debug(f"Adding {role} message to chat history")
        chat_history.append({"role": role, "content": content})
        config.save_chat_log(chat_history)
        logger.info("Chat history updated successfully")
        return chat_history
    except Exception as e:
        logger.error(f"Error updating chat history: {e}", exc_info=True)
        return chat_history

def categorize_action(text: str) -> str:
    """Determine type of action based on user input"""
    try:
        logger.debug(f"Categorizing action for input: {text}")
        text = text.lower()
        if "generate image" in text or "create image" in text:
            action = "image"
        elif "search" in text or "find" in text:
            action = "search"
        else:
            action = "chat"
        logger.debug(f"Action categorized as: {action}")
        return action
    except Exception as e:
        logger.error(f"Error categorizing action: {e}", exc_info=True)
        return "chat"

def modify_answer(answer: str) -> str:
    """Clean and format the model's response"""
    try:
        logger.debug(f"Modifying answer: {answer}")
        # Remove any leading/trailing whitespace
        answer = answer.strip()
        
        # Remove any "Assistant:" prefix if present
        if answer.startswith("Assistant:"):
            answer = answer[len("Assistant:"):].strip()
            
        # Ensure proper spacing after punctuation
        for punct in ".!?":
            answer = answer.replace(f"{punct}", f"{punct} ")
        answer = " ".join(answer.split())
        
        logger.debug(f"Modified answer: {answer}")
        return answer
    except Exception as e:
        logger.error(f"Error modifying answer: {e}", exc_info=True)
        return answer

def query(prompt: str, chat_history: List[dict]) -> Dict[str, Any]:
    """
    Process user query and return structured response
    
    Args:
        prompt (str): User's input prompt
        chat_history (List[dict]): Chat history
        
    Returns:
        Dict[str, Any]: Response containing action and content
    """
    try:
        start_time = time.time()
        logger.info(f"Processing query: {prompt[:50]}...")
        
        # Get categorized actions from FirstLayerDMM
        actions = FirstLayerDMM(prompt)
        logger.debug(f"Categorized actions: {actions}")
        
        # Initialize clients
        cohere_client = initialize_cohere()
        groq_client = groq.Groq(api_key=config.api.groq_api_key)
        
        if not cohere_client or not groq_client:
            raise Exception("Failed to initialize API clients")

        # Process prompt with chat history
        processed_prompt = process_prompt(prompt, chat_history)
        
        # Generate response using appropriate model based on action type
        primary_action = actions[0] if actions else "chat"
        if primary_action.startswith("general"):
            completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": processed_prompt}],
                model=config.models.groq_model,
            )
            response = completion.choices[0].message.content
        else:
            response = cohere_client.generate(
                prompt=processed_prompt,
                model=config.models.cohere_model,
                max_tokens=300,
            ).generations[0].text

        # Clean and format response
        response = modify_answer(response)
        
        # Update chat history
        chat_history = add_to_chat_history("user", prompt, chat_history)
        chat_history = add_to_chat_history("assistant", response, chat_history)
        
        elapsed = time.time() - start_time
        logger.info(f"Query processed in {elapsed:.2f}s")
        
        return {
            "action": actions[0] if actions else "chat",
            "content": response,
            "success": True,
            "all_actions": actions
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {
            "action": "error",
            "content": f"An error occurred: {str(e)}",
            "success": False,
            "all_actions": []
        }

# Interactive testing mode
if __name__ == "__main__":
    logger.info("Starting interactive testing mode")
    chat_history = config.load_chat_log()
    
    try:
        while True:
            user_input = input("\nEnter your message (or 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break
                
            result = query(user_input, chat_history)
            print(f"\nAction: {result['action']}")
            print(f"All Actions: {result['all_actions']}")
            print(f"Response: {result['content']}")
            
    except KeyboardInterrupt:
        logger.info("Interactive testing mode terminated by user")
    except Exception as e:
        logger.error(f"Error in interactive testing mode: {e}")
    finally:
        logger.info("Interactive testing mode ended")