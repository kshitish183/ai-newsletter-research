from pydantic import BaseModel
from typing import List, Optional


class ArticleAnalysis(BaseModel):
    url: Optional[str] = None
    title: str
    category: Optional[str] = "Psyche Guides"
    summary: str
    main_idea: str
    key_insights: List[str]
    important_concepts: List[str]
    practical_takeaways: List[str]
    difficulty: str
    level: Optional[str] = None