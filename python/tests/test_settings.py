"""
Tests for settings module.
"""

import pytest
import os
from unittest.mock import patch
from settings import Config

class TestConfig:
    
    def test_load_from_env_vars(self):
        """Should load configuration from environment variables."""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://env.supabase.co",
            "SUPABASE_KEY": "env-key",
            "BUCKET_NAME": "env-bucket"
        }):
            cfg = Config.load()
            assert cfg.supabase_url == "https://env.supabase.co"
            assert cfg.supabase_key == "env-key"
            assert cfg.bucket_name == "env-bucket"

    def test_validation_failure(self):
        """Should raise error if required fields missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Mock legacy config to be empty if it exists
            with patch("settings.legacy_config", None):
                cfg = Config.load()
                with pytest.raises(ValueError, match="Missing SUPABASE_URL"):
                    cfg.validate()

    def test_roboflow_config(self):
        """Should load Roboflow config."""
        with patch.dict(os.environ, {
            "ROBOFLOW_API_KEY": "rf-key",
            "ROBOFLOW_MODEL_ID": "rf-model",
            "ROBOFLOW_CONFIDENCE": "0.5"
        }):
            cfg = Config.load()
            assert cfg.roboflow_api_key == "rf-key"
            assert cfg.roboflow_model_id == "rf-model"
            assert cfg.roboflow_confidence == 0.5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
