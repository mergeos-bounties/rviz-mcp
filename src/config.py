class Config:
    def __init__(self):
        self.remote_api_url = "http://localhost:5000"
        self.timeout = 30
        self.retry_attempts = 3

    def update(self, config_dict):
        """Update configuration with a dictionary"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)