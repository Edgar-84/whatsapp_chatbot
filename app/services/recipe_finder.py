from rapidfuzz import process
from app.config.logger_settings import get_logger

logger = get_logger(__name__)


class RecipeFinder:
    def __init__(self, known_ingredients: list[str]):
        self.known_ingredients = known_ingredients

    async def find_recipes_by_ingredients(self, user_input: str, similarity_threshold: int = 80) -> list[str] | None:
        """
        Main service method for finding recipes by ingredients
        """

        # 1. Extract potential ingredients from text
        possible_ingredients = self._extract_words(user_input)
        logger.info(f"Extracted ingredients: {possible_ingredients}")

        # 2. Fuzzy matching
        corrected_ingredients = []
        for word in possible_ingredients:
            matches = process.extract(word, self.known_ingredients)
            for match, score, _ in matches:
                if score >= similarity_threshold:
                    corrected_ingredients.append(match)

        # 3. Check if we found anything
        if not corrected_ingredients:
            logger.warning(f"No ingredients found in user input: {user_input}")
            return None
        
        logger.info(f"Found ingredients: {corrected_ingredients}")
        return corrected_ingredients

        # # 4. Find recipes for each ingredient
        # recipe_sets = []
        # for ing in corrected_ingredients:
        #     recipe_ids = await self.db_client.get_recipe_ids_by_ingredient(ing)
        #     if recipe_ids:
        #         recipe_sets.append(set(recipe_ids))

        # if not recipe_sets:
        #     return {"status": "error", "message": "לא מצאנו מתכונים מתאימים."}

        # # 5. Try to find recipes by intersection of all ingredients
        # matching_recipe_ids = set.intersection(*recipe_sets)
        # if matching_recipe_ids:
        #     recipes = await self.db_client.get_recipes_by_ids(matching_recipe_ids)
        #     return {"status": "success", "recipes": recipes}

        # # 6. If not successful - fallback: search for recipes containing at least 1 ingredient
        # recipes_union = set.union(*recipe_sets)
        # recipes = await self.db_client.get_recipes_by_ids(recipes_union)
        # if recipes:
        #     return {"status": "partial", "recipes": recipes, "message": "לא מצאנו את כל הרכיבים, אך מצאנו חלק."}

        # # 7. If nothing found - error
        # return {"status": "error", "message": "לא נמצאו מתכונים."}

    def _extract_words(self, text: str) -> list:
        """
        Simple parser for splitting text into words
        Can be replaced with more advanced NLP parsing
        """
        import re
        words = re.findall(r'\w+', text)  # Finds words in Hebrew and English
        return words
