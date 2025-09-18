#!/usr/bin/env python3
"""
Universal Backrooms Initialization Script
Provides setup and initialization for the UniversalBackrooms project.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.7 or higher."""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def create_env_file():
    """Create .env file from example if it doesn't exist."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(".env.example", ".env")
            print("✓ Created .env file from .env.example")
            print("  Please add your API keys to the .env file")
        else:
            # Create a basic .env template
            with open(".env", "w") as f:
                f.write("# API Keys for UniversalBackrooms\n")
                f.write("ANTHROPIC_API_KEY=your_anthropic_key_here\n")
                f.write("OPENAI_API_KEY=your_openai_key_here\n")
                f.write("WORLD_INTERFACE_KEY=your_world_interface_key_here\n")
            print("✓ Created .env template file")
            print("  Please add your API keys to the .env file")
    else:
        print("✓ .env file already exists")

def install_python_dependencies():
    """Install Python dependencies from requirements.txt."""
    if not Path("requirements.txt").exists():
        print("Warning: requirements.txt not found, skipping Python dependencies")
        return
    
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix or hasattr(sys, 'real_prefix')
    
    if not in_venv:
        print("⚠ Not in a virtual environment")
        print("  Consider creating one with: python3 -m venv backrooms_env")
        print("  Then activate with: source backrooms_env/bin/activate")
        print("  Attempting to install with --user flag...")
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"], 
                          check=True, capture_output=True, text=True)
            print("✓ Python dependencies installed (user-level)")
        except subprocess.CalledProcessError as e:
            print(f"Error installing Python dependencies: {e}")
            print("You may need to create a virtual environment or use --break-system-packages")
            print("Run: python3 -m venv backrooms_env && source backrooms_env/bin/activate")
    else:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                          check=True, capture_output=True, text=True)
            print("✓ Python dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"Error installing Python dependencies: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")

def install_node_dependencies():
    """Install Node.js dependencies if package.json exists."""
    if not Path("package.json").exists():
        print("Note: No package.json found, skipping Node.js dependencies")
        return
    
    try:
        subprocess.run(["npm", "install"], check=True, capture_output=True, text=True)
        print("✓ Node.js dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Node.js dependencies: {e}")
        print("Make sure Node.js and npm are installed")
    except FileNotFoundError:
        print("Note: npm not found, skipping Node.js dependencies")

def create_directories():
    """Create necessary directories."""
    directories = ["BackroomsLogs", "backrooms_env"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Directory {directory} ready")

def verify_api_keys():
    """Check if API keys are configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    keys_status = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "WORLD_INTERFACE_KEY": os.getenv("WORLD_INTERFACE_KEY")
    }
    
    configured_keys = []
    missing_keys = []
    
    for key, value in keys_status.items():
        if value and value != f"your_{key.lower()}_here":
            configured_keys.append(key)
        else:
            missing_keys.append(key)
    
    if configured_keys:
        print(f"✓ Configured API keys: {', '.join(configured_keys)}")
    
    if missing_keys:
        print(f"⚠ Missing API keys: {', '.join(missing_keys)}")
        print("  Add these to your .env file to use all features")

def main():
    """Main initialization function."""
    print("🔄 Initializing UniversalBackrooms...")
    print()
    
    # Check Python version
    check_python_version()
    
    # Create .env file
    create_env_file()
    
    # Create directories
    create_directories()
    
    # Install dependencies
    install_python_dependencies()
    install_node_dependencies()
    
    # Verify API keys
    verify_api_keys()
    
    print()
    print("🎉 Initialization complete!")
    print()
    print("Next steps:")
    print("1. Add your API keys to the .env file")
    print("2. Run: python backrooms.py")
    print("3. Or run with specific models: python backrooms.py --lm opus gpt4o")
    print()
    print("For more options, run: python backrooms.py --help")

if __name__ == "__main__":
    main()