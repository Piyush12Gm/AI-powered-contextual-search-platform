from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ProductIn(BaseModel):
    title: str
    description: str
    category: str
    brand: str
    attributes: Dict[str, str] = Field(default_factory=dict)
    price: float
    rating: float = 0

class ProductOut(ProductIn):
    id: int

class SearchQuery(BaseModel):
    q: str
    filters: Dict[str, str | float | List[str]] = Field(default_factory=dict)
    top_k: int = 20

class SearchResult(BaseModel):
    product: ProductOut
    score: float
    explanation: Optional[str] = None

class EventIn(BaseModel):
    type: str
    payload: Dict