from app.database.supabase_client import SupabaseClient
from app.api.dtos.food_dtos import FoodDTO
from app.config.logger_settings import get_logger

logger = get_logger(__name__)


class FoodRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "foods"
    
    async def get_food(self, query: dict) -> FoodDTO | None:
        result = await self.client.read(self.table, query)
        if len(result) == 0:
            return None
        return FoodDTO(**result[0])

    async def get_foods_by_list_lab_codes(self, lab_codes: list[str]) -> list[FoodDTO]:
        result = await self.client.read(self.table, {"lab_code": {"in": lab_codes}})
        return [FoodDTO(**food) for food in result] if result else []

    async def get_grouped_foods_by_recipe_id(self, recipe_id: int) -> list[dict[str, list[str]]]:
        """
        Get products grouped by groups for recipe by recipe_id
        """
        # Step 1: Get food_id from table recipes_foods by recipe_id
        recipe_foods = await self.client.read("recipes_foods", {"recipe_id": recipe_id})
        # logger.info(f"Recipe foods: {recipe_foods}")
        if not recipe_foods:
            return []

        food_ids = [item["food_id"] for item in recipe_foods]
        # logger.info(f"food id: {food_ids}")

        # Step 2: Get data from table foods by these food_id
        foods = await self.client.read("foods", {"id": {"in": food_ids}})
        # logger.info(f"foods: {foods}")
        if not foods:
            return []

        # Step 3: Get all food_groups by unique food_group_id
        food_group_ids = list(set(food["food_group_id"] for food in foods))
        food_groups = await self.client.read("foods_groups", {"id": {"in": food_group_ids}})
        # logger.info(f"food groups: {food_groups}")
        food_group_map = {group["id"]: group["name"] for group in food_groups}
        # logger.info(f"food group map: {food_group_map}")
        
        # Step 4: Group products by groups
        grouped = {}
        for food in foods:
            group_name = food_group_map.get(food["food_group_id"], "Unknown")
            grouped.setdefault(group_name, []).append(food["name"])

        # Step 5: Convert to the required format
        result = [{"food_group_name": group, "foods": names} for group, names in grouped.items()]
        # logger.info(f"Result: {result}")
        return result

