"""User preferences schema definitions"""
from pydantic import BaseModel, Field, confloat


class NotificationPreferences(BaseModel):
    """通知偏好设置 - 按类别开关"""
    GAME: bool = Field(default=True, description="游戏类通知（游戏开始、结束等）")
    ROOM: bool = Field(default=True, description="房间类通知（玩家加入、房间创建等）")
    SOCIAL: bool = Field(default=True, description="社交类通知（好友请求等）")
    SYSTEM: bool = Field(default=True, description="系统类通知（公告、维护等）")

    class Config:
        json_schema_extra = {
            "example": {
                "GAME": True,
                "ROOM": True,
                "SOCIAL": True,
                "SYSTEM": True
            }
        }


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
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)

    class Config:
        json_schema_extra = {
            "example": {
                "sound_effects": {
                    "enabled": True,
                    "volume": 0.8,
                    "muted": False
                },
                "notifications": {
                    "GAME": True,
                    "ROOM": True,
                    "SOCIAL": True,
                    "SYSTEM": True
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
                    },
                    "notifications": {
                        "GAME": True,
                        "ROOM": True,
                        "SOCIAL": True,
                        "SYSTEM": True
                    }
                }
            }
        }
