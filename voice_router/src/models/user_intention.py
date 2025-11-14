from typing import List, Optional, Any
from pydantic import BaseModel

class ApiParameter(BaseModel):
    parameter_name: str
    default_value: Any = None
    allowed_values: List[Any] = []


class ApiMatch(BaseModel):
    api_uri: str
    score: float
    voice_form: Optional[str]
    text_form: Optional[str]
    parameters: List[ApiParameter] = []

