from pydantic import BaseModel, Field
from typing import Any, Dict, List, Union

class SummarizeRequest(BaseModel):
    payload: Union[Dict[str, Any], List[Any]] = Field(..., description="Input JSON content to summarize associated with social media data.")
