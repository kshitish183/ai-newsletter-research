from pydantic import BaseModel
from typing import List


class ArticleAnalysis(BaseModel):
    title: str
    summary: str
    main_idea: str
    key_insights: List[str]
    important_concepts: List[str]
    practical_takeaways: List[str]
    difficulty: str