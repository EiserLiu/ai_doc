from pydantic import BaseModel, Field


class NotifyConfigCreate(BaseModel):
    notify_type: str = Field(..., pattern="^(feishu|wecom|dingtalk)$")
    webhook_url: str = Field(..., max_length=1024)
    is_enabled: bool = True


class NotifyConfigUpdate(BaseModel):
    webhook_url: str | None = Field(default=None, max_length=1024)
    is_enabled: bool | None = None


class NotifyConfigResponse(BaseModel):
    id: int
    notify_type: str
    webhook_url: str
    is_enabled: bool

    class Config:
        from_attributes = True


class NotifyTestRequest(BaseModel):
    notify_type: str = Field(..., pattern="^(feishu|wecom|dingtalk)$")
    webhook_url: str
