import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Successfully installed dependencies!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    directories = [
        "Data",
        "Frontend/Files",
        "Frontend/Graphics",
        "Logs"
    ]
    
    print("Creating required directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("Successfully created directories!")

def create_env_template():
    """Create a template .env file if it doesn't exist"""
    env_path = Path(".env")
    if not env_path.exists():
        print("Creating .env template...")
        with open(env_path, "w") as f:
            f.write("""# API Keys (Required)
CohereAPIKey=your_cohere_api_key_here
GroqAPIKey=your_groq_api_key_here
HuggingfaceAPIKey=your_huggingface_api_key_here  # Optional

# Assistant Configuration
Username=User
Assistantname=EVA
InputLanguage=en-US
AssistantVoice=en-CA-LiamNeural

# Environment
ENVIRONMENT=development  # Options: development, testing, production
""")
        print("Created .env template! Please edit it with your API keys.")
    else:
        print(".env file already exists, skipping creation.")

def main():
    """Main setup function"""
    print("Starting EVA DDM setup...")
    
    # Install dependencies
    install_dependencies()
    
    # Create directories
    create_directories()
    
    # Create .env template
    create_env_template()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Edit the .env file with your API keys")
    print("2. Run 'python Main.py' to start the assistant")
    print("\nFor more information, check the documentation in docs/configuration.md")

if __name__ == "__main__":
    main() 