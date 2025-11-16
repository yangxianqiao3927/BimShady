import os
from dotenv import load_dotenv

# ============================================
# METHOD 1: Using python-dotenv (Recommended)
# ============================================

# Load .env file from current directory
load_dotenv()

# Read environment variables
api_key = os.getenv('ANTHROPIC_API_KEY')
database_url = os.getenv('DATABASE_URL')
debug_mode = os.getenv('DEBUG', 'False')  # Default value if not found

print("Method 1 - Using python-dotenv:")
print(f"API Key: {api_key}")
print(f"Database URL: {database_url}")
print(f"Debug Mode: {debug_mode}")
print()

# ============================================
# METHOD 2: Load from specific .env file path
# ============================================

from dotenv import load_dotenv
from pathlib import Path

# Specify custom .env file location
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Or use absolute path
# load_dotenv(dotenv_path='/path/to/your/.env')

print("Method 2 - Custom path:")
print(f"API Key: {os.getenv('ANTHROPIC_API_KEY')}")
print()

# ============================================
# METHOD 3: Load into a dictionary
# ============================================

from dotenv import dotenv_values

# Load all variables into a dictionary
config = dotenv_values(".env")

print("Method 3 - Dictionary:")
print(f"All config values: {config}")
print(f"API Key from dict: {config.get('ANTHROPIC_API_KEY')}")
print()

# ============================================
# METHOD 4: Override existing environment variables
# ============================================

# By default, existing env vars take precedence
# Use override=True to replace them
load_dotenv(override=True)

print("Method 4 - With override:")
print(f"API Key: {os.getenv('ANTHROPIC_API_KEY')}")
print()

# ============================================
# METHOD 5: Check if variable exists
# ============================================

if 'ANTHROPIC_API_KEY' in os.environ:
    print("✓ ANTHROPIC_API_KEY is set")
else:
    print("✗ ANTHROPIC_API_KEY is not set")


# ============================================
# METHOD 6: Read .env file manually (without python-dotenv)
# ============================================

def load_env_manually(filepath='.env'):
    """
    Manually parse .env file without external libraries
    """
    env_vars = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Split on first = sign
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        env_vars[key.strip()] = value
                        # Also set in os.environ
                        os.environ[key.strip()] = value
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")

    return env_vars


print("Method 6 - Manual parsing:")
manual_config = load_env_manually('.env')
print(f"Manually loaded config: {manual_config}")
print()


# ============================================
# EXAMPLE: Complete usage pattern
# ============================================

def get_config():
    """
    Recommended pattern for loading configuration
    """
    # Load .env file
    load_dotenv()

    # Get required variables with error handling
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    # Get optional variables with defaults
    config = {
        'api_key': api_key,
        'database_url': os.getenv('DATABASE_URL', 'sqlite:///default.db'),
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        'port': int(os.getenv('PORT', '8000')),
    }

    return config


# Usage
try:
    config = get_config()
    print("Complete config pattern:")
    print(f"Config: {config}")
except ValueError as e:
    print(f"Configuration error: {e}")