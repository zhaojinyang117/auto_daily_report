import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration dictionary
CONFIG = {
    # Gemini API configuration
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    # Telegram configuration
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    # Personal information configuration
    "USER_NAME": os.getenv("USER_NAME"),
    "EMAIL_SIGNATURE_NAME": os.getenv("EMAIL_SIGNATURE_NAME"),
    "EMAIL_SIGNATURE_PHONE": os.getenv("EMAIL_SIGNATURE_PHONE"),
    # Email configuration
    "EMAIL_FROM": os.getenv("EMAIL_FROM"),
    "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
    "EMAIL_TO": os.getenv("EMAIL_TO"),
    # SMTP configuration
    "SMTP_SERVER": os.getenv("SMTP_SERVER"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "465")),  # Convert to integer
    # Log configuration
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),  # Keep default value
    "LOG_FILE": os.getenv("LOG_FILE", "alice studio_email_logs.txt"),  # Keep default value
}

# Define required configurations for different modes
def get_required_configs_for_mode(mode="full"):
    """Get required configuration items based on mode
    
    Args:
        mode: 'full' for complete functionality, 'preview' for preview-only mode
    
    Returns:
        list: Required configuration keys for the mode
    """
    if mode == "preview":
        # For preview mode, we only need basic user info (can use defaults if missing)
        return []
    else:
        # For full mode, we need all email-related configs
        return [
            "EMAIL_FROM",
            "EMAIL_PASSWORD", 
            "EMAIL_TO",
            "SMTP_SERVER",
            "SMTP_PORT",
            "USER_NAME",
            "EMAIL_SIGNATURE_NAME",
            "EMAIL_SIGNATURE_PHONE",
        ]

def validate_config(mode="full"):
    """Validate configuration based on mode"""
    required_configs = get_required_configs_for_mode(mode)
    
    for config_name in required_configs:
        if not CONFIG.get(config_name):
            raise ValueError(f"缺少必要的配置项: {config_name}")

# Validate necessary configurations for full mode by default
# This will be called conditionally based on the mode
try:
    validate_config("full")
except ValueError:
    # If full validation fails, we'll handle it in the application logic
    pass


# Add Config class
class Config:
    """Configuration class for providing configuration access interface"""

    def __init__(self, mode="full"):
        """Initialize configuration
        
        Args:
            mode: 'full' for complete functionality, 'preview' for preview-only mode
        """
        self.config = CONFIG
        self.mode = mode
        
        # Validate configuration based on mode
        if mode == "full":
            validate_config("full")

    def get(self, key, default=None):
        """Get configuration value"""
        value = self.config.get(key, default)
        # If the value is None but we have a default, use the default
        if value is None and default is not None:
            return default
        return value

    def __getattr__(self, name):
        """Access configuration through attribute"""
        return self.config.get(name)
