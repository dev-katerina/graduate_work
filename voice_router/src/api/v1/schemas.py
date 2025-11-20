from typing import List, Optional, Any
from pydantic import BaseModel, Field

class ApiParameter(BaseModel):
    parameter_name: str
    default_value: Any = None
    allowed_values: List[Any] = []


class ApiMatch(BaseModel):
    api_uri: str
    voice_form: Optional[str]
    text_form: Optional[str]
    description: List[str]
    parameters: List[ApiParameter] = []

class ReadAPIMatch(ApiMatch):
    id: str