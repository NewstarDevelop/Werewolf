"""User preferences schema definitions"""
from pydantic import BaseModel, Field, confloat


class SoundEffectsPreferences(BaseModel):
    """音效偏好设置"""
    enabled: bool = Field(default=True, description="是否启用音效")
    volume: confloat(ge=0.0, le=1.0) = Field(default=1.0, description="音量（0.0-1.0）")
    muted: bool = Field(default=False, description="是否静音")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "volume": 0.8,
                "muted": False
            }
        }


class UserPreferences(BaseModel):
    """用户偏好设置（可扩展）"""
    sound_effects: SoundEffectsPreferences = Field(default_factory=SoundEffectsPreferences)

    class Config:
        json_schema_extra = {
            "example": {
                "sound_effects": {
                    "enabled": True,
                    "volume": 0.8,
                    "muted": False
                }
            }
        }


class UserPreferencesResponse(BaseModel):
    """用户偏好响应"""
    preferences: UserPreferences

    class Config:
        json_schema_extra = {
            "example": {
                "preferences": {
                    "sound_effects": {
                        "enabled": True,
                        "volume": 0.8,
                        "muted": False
                    }
                }
            }
        }
