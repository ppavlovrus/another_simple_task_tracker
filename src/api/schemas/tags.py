from typing import Optional
from pydantic import BaseModel
from typing_extensions import Annotated
from pydantic import StringConstraints

NameStr = Annotated[
    str,
    StringConstraints(min_length=1, max_length=100, strip_whitespace=True)
]

class TagCreate(BaseModel):
    """Request for tag creation"""
    name: NameStr

class TagUpdate(BaseModel):
    """Request for refresh tag"""
    id: int
    name: Optional[NameStr] = None

class TagResponse(BaseModel):
    """Request for tags"""
    id: int
    name: str