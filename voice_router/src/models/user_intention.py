from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ApiMatch(BaseModel):
    api_uri: str
    score: float
    voice_form: Optional[str] = None
    text_form: Optional[str] = None
    parameters: List[str] = None
