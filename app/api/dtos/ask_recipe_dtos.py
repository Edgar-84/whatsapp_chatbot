from typing import Optional

from app.lib.dto.base_dto import Base


class AskRecipeAnswerDTO(Base):
    prompt_for_llm: Optional[str] = None
    ai_result_recipe_details: Optional[str] = None
    ai_result_recomendation: Optional[str] = None
    ai_result_recipe_id: Optional[int] = None
    ai_result_recipe_name: Optional[str] = None
    recipes_id_from_rag: Optional[list[int]] = None # Recipes id from RAG
    filtered_disliked_recipes_id: Optional[list[int]] = None
    filtered_restrictions_recipes_id: Optional[list[int]] = None
    recipes_id_after_filter: Optional[list[int]] = None
    recipes_after_filter: Optional[list[dict]] = None # Recipes which will be analyzed by LLM
