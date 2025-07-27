from pydantic import BaseModel
from typing import Optional, List

class DTSearch(BaseModel):
    value: Optional[str] = None

class DTOrder(BaseModel):
    column: int
    dir: str

class DTColumn(BaseModel):
    data: str
    name: str
    searchable: bool

class ListRequest(BaseModel):
    start: int = 0
    length: int = 10
    search: DTSearch
    order: List[DTOrder]
    columns: List[DTColumn]
