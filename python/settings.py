"""
Enhanced Configuration Management.
"""

import os
from dataclasses import dataclass
from typing import Optional

# Try to import legacy config
try:
    import config as legacy_config
except ImportError:
    legacy_config = None

@dataclass
class Config:
    """Application Configuration."""
    supabase_url: str
    supabase_key: str
    bucket_name: str
    photo_dir: str = "photos"
    roboflow_api_key: Optional[str] = None
    roboflow_model_id: Optional[str] = None
    roboflow_confidence: float = 0.8
    vercel_app_url: str = "https://excel-mascot.vercel.app/"

    @classmethod
    def load(cls):
        """
        Load configuration from Environment Variables, then legacy config.py.
        """
        # 1. Defaults from Legacy Config
        url = getattr(legacy_config, "SUPABASE_URL", "")
        key = getattr(legacy_config, "SUPABASE_KEY", "")
        bucket = getattr(legacy_config, "BUCKET_NAME", "photos")
        
        # 2. Override with Env Vars
        url = os.environ.get("SUPABASE_URL", url) or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", key) or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
        bucket = os.environ.get("BUCKET_NAME", bucket)
        
        roboflow_key = os.environ.get("ROBOFLOW_API_KEY")
        roboflow_model = os.environ.get("ROBOFLOW_MODEL_ID")
        roboflow_conf = float(os.environ.get("ROBOFLOW_CONFIDENCE", "0.8"))
        
        vercel_url = os.environ.get("VERCEL_APP_URL") or os.environ.get("NEXT_PUBLIC_VERCEL_URL", "https://excel-mascot.vercel.app/")
        
        return cls(
            supabase_url=url,
            supabase_key=key,
            bucket_name=bucket,
            roboflow_api_key=roboflow_key,
            roboflow_model_id=roboflow_model,
            roboflow_confidence=roboflow_conf,
            vercel_app_url=vercel_url
        )

    def validate(self):
        """Validate critical configuration."""
        errors = []
        if not self.supabase_url:
            errors.append("Missing SUPABASE_URL")
        if not self.supabase_key:
            errors.append("Missing SUPABASE_KEY")
            
        if errors:
            raise ValueError(f"Configuration Invalid: {', '.join(errors)}")
        return True

# Singleton instance
settings = Config.load()
