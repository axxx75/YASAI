from enum import Enum
from pydantic import BaseModel, Field

class TaskCategory(str, Enum):
    CODING = "coding"
    REASONING = "reasoning"
    GENERAL = "general"
    FAST_CHECK = "fast_check"

class RoutingDecision(BaseModel):
    category: TaskCategory = Field(
        ..., 
        description="Categoria del task identificata dal Router"
    )
    selected_model: str = Field(
        ..., 
        description="Identificativo esatto del modello OpenRouter da utilizzare"
    )
    confidence: float = Field(
        ..., 
        description="Punteggio di confidenza da 0.0 a 1.0"
    )
    reasoning: str = Field(
        ..., 
        description="Spiegazione sintetica della scelta del modello"
    )