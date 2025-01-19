# Import required packages
import asyncio
from random import randint
from PIL import Image
import requests
import os
import time
import logging
from Backend.Config import config
from Backend.LogConfig import setup_logging

# Initialize logger
logger = logging.getLogger("ImageGeneration")

def open_images(prompt: str) -> str:
    """
    Generate and open an image based on the prompt
    
    Args:
        prompt (str): Description of the image to generate
        
    Returns:
        str: Path to the generated image
    """
    try:
        start_time = time.time()
        logger.info(f"Generating image for prompt: {prompt}")
        
        # Create filename from prompt
        filename = "_".join(prompt.split()[:3]) + ".png"
        filepath = os.path.join(config.paths.data_dir, filename)
        
        # Set up API request
        API_URL = f"https://api-inference.huggingface.co/models/{config.models.stable_diffusion_model}"
        headers = {"Authorization": f"Bearer {config.api.huggingface_api_key}"}
        
        # Make API request
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return ""
            
        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        # Update status file
        with open(config.paths.image_gen_status_path, 'w') as f:
            f.write("1")
            
        elapsed = time.time() - start_time
        logger.info(f"Image generated successfully in {elapsed:.2f}s: {filepath}")
        
        # Open image
        image = Image.open(filepath)
        image.show()
        
        return filepath
        
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        # Update status file to indicate error
        with open(config.paths.image_gen_status_path, 'w') as f:
            f.write("0")
        return ""

def query(prompt: str) -> dict:
    """
    Process image generation query
    
    Args:
        prompt (str): Description of the image to generate
        
    Returns:
        dict: Response containing status and file path
    """
    try:
        start_time = time.time()
        logger.info(f"Processing image query: {prompt}")
        
        # Generate and open image
        filepath = open_images(prompt)
        
        elapsed = time.time() - start_time
        if filepath:
            logger.info(f"Image query processed successfully in {elapsed:.2f}s")
            return {
                "success": True,
                "filepath": filepath,
                "message": "Image generated successfully"
            }
        else:
            logger.error("Image generation failed")
            return {
                "success": False,
                "filepath": "",
                "message": "Failed to generate image"
            }
            
    except Exception as e:
        logger.error(f"Error processing image query: {e}")
        return {
            "success": False,
            "filepath": "",
            "message": f"Error: {str(e)}"
        }

# Interactive testing mode
if __name__ == "__main__":
    logger.info("Starting interactive testing mode")
    
    try:
        while True:
            prompt = input("\nEnter image description (or 'exit' to quit): ")
            if prompt.lower() == 'exit':
                break
                
            result = query(prompt)
            print(f"\nSuccess: {result['success']}")
            print(f"File: {result['filepath']}")
            print(f"Message: {result['message']}")
            
    except KeyboardInterrupt:
        logger.info("Interactive testing mode terminated by user")
    except Exception as e:
        logger.error(f"Error in interactive testing mode: {e}")
    finally:
        logger.info("Interactive testing mode ended")

# Initialize Hugging Face API settings
API_URL = f"https://api-inference.huggingface.co/models/{config.models.stable_diffusion_model}"
headers = {"Authorization": f"Bearer {config.api.huggingface_api_key}"}
logger.info(f"Initialized Hugging Face API with model: {config.models.stable_diffusion_model}")

async def generate_images(prompt: str):
    """
    Generate multiple images asynchronously using the Stable Diffusion model.
    
    Args:
        prompt (str): Text prompt for image generation
    """
    try:
        start_time = time.time()
        logger.info(f"Starting image generation for prompt: {prompt}")
        tasks = []

        # Create tasks for parallel image generation
        for i in range(4):
            seed = randint(0, 1000000)
            enhanced_prompt = f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed = {seed}"
            payload = {"inputs": enhanced_prompt}
            
            logger.debug(f"Creating task {i+1} with seed {seed}")
            task = asyncio.create_task(query(payload))
            tasks.append(task)

        # Wait for all tasks to complete
        logger.debug("Waiting for all image generation tasks to complete")
        image_bytes_list = await asyncio.gather(*tasks)

        # Save generated images
        for i, image_bytes in enumerate(image_bytes_list):
            output_path = f"Data/{prompt.replace(' ', '_')}{i + 1}.jpg"
            logger.debug(f"Saving image {i+1} to {output_path}")
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
        elapsed_time = time.time() - start_time
        logger.info(
            f"Successfully generated and saved {len(image_bytes_list)} images - "
            f"response_time={elapsed_time:.2f}"
        )
        
    except Exception as e:
        logger.error(f"Error in generate_images: {e}", exc_info=True)
        raise

def GenerateImages(prompt: str):
    """
    Main function to generate and display images.
    
    Args:
        prompt (str): Text prompt for image generation
    """
    try:
        start_time = time.time()
        logger.info(f"Starting image generation process for prompt: {prompt}")
        
        asyncio.run(generate_images(prompt))
        open_images(prompt)
        
        elapsed_time = time.time() - start_time
        logger.info(
            f"Image generation and display completed successfully - "
            f"response_time={elapsed_time:.2f}"
        )
        
    except Exception as e:
        logger.error(f"Error in GenerateImages: {e}", exc_info=True)
        raise

def main():
    """Main execution loop for image generation service"""
    logger.info("Starting image generation service")
    
    while True:
        try:
            # Read image generation status
            with open(config.paths.image_gen_status_path, "r") as f:
                Data: str = f.read()
            Prompt, Status = Data.split(",")

            # Generate images if status is True
            if Status.strip() == "True":
                logger.info(f"Received generation request for prompt: {Prompt}")
                GenerateImages(prompt=Prompt)

                # Reset status after generation
                logger.debug("Resetting generation status")
                with open(config.paths.image_gen_status_path, "w") as f:
                    f.write("False,False")
                break
            else:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(1)  # Prevent rapid retries on error

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Service terminated by user")
    except Exception as e:
        logger.error(f"Service terminated due to error: {e}", exc_info=True)