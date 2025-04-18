from typing import Optional
from enum import Enum
from app.utils.cache.abstract_cache import AbstractUserCache
from app.api.dtos.recipe_user_preferences_dto import RecipeUserPreferencesDTO

class UserStates(str, Enum):
    AWAITING_VERIFICATION = "awaiting_verification"  # Waiting for verification
    MAIN_MENU = "main_menu"  # Main menu
    MY_RESULT_MENU = "my_result_menu"  # View My Results
    MY_RESTRICTIONS_MENU = "my_restrictions_menu"  # See My Restrictions

    ASK_USER_WHANT_RECIPES = "ask_user_whant_recipes"  # Ask user want recipes
    CHOICE_MEAL_TYPE_MENU = "choice_meal_type_menu"  # After choose Meal Type
    DIETARY_PREFERENCE_FILTER = "dietary_preference_filter"  # Dietary Preference Filter
    INCLUDE_INGREDIENTS_FILTER = "include_ingredients_filter"  # Include Ingredients Filter
    USER_WAITING_ANSWER = "user_waiting_answer"  # Set User to Waiting answer state
    SHOW_PERSONALIZED_RECIPES_MENU = "show_personalized_recipes_menu"  # When return fit recipes
    ASK_WHY_DISLIKE = "ask_why_dislike"  # Ask user why dislike
    MENU_SAVE_RECIPE = "menu_save_recipe"  # Menu to save recipe

    NUTRITION_ASSISTANT_MENU = "nutrition_assistant_menu"  # Personal Nutrition Assistant



class UserSession:
    def __init__(self, cache: AbstractUserCache, whatsapp_number: str):
        self.cache = cache
        self.whatsapp_number = whatsapp_number
        self._data: Optional[dict] = None

    async def _load(self):
        if self._data is None:
            self._data = await self.cache.get(self.whatsapp_number)
            if self._data is None:
                self._data = {
                    "user": None,
                    "state": UserStates.AWAITING_VERIFICATION,
                    "user_recipe_preference": None,
                    "get_recipe_id": None,
                    "restrictions_lab_codes": None,
                    "personalized_recipes": None,
                    "high_sensitivity_foods": None,
                    "low_sensitivity_foods": None,
                    "all_restriction_products": None,
                }

    async def get(self, key: str):
        await self._load()
        return self._data.get(key)

    async def set(self, key: str, value):
        await self._load()
        self._data[key] = value
        await self._save()

    async def update(self, **kwargs):
        await self._load()
        self._data.update(kwargs)
        await self._save()

    async def get_state(self) -> UserStates:
        await self._load()
        return self._data.get("state", UserStates.AWAITING_VERIFICATION)

    async def set_state(self, state: UserStates):
        await self.set("state", state)

    async def get_user(self):
        return await self.get("user")

    async def set_user(self, user_obj):
        await self.set("user", user_obj)
    
    async def get_high_sensitivity_foods(self):
        return await self.get("high_sensitivity_foods")
    
    async def set_high_sensitivity_foods(self, high_sensitivity_foods):
        await self.set("high_sensitivity_foods", high_sensitivity_foods)
    
    async def get_low_sensitivity_foods(self):
        return await self.get("low_sensitivity_foods")
    
    async def set_low_sensitivity_foods(self, low_sensitivity_foods):
        await self.set("low_sensitivity_foods", low_sensitivity_foods)
    
    async def get_restrictions_lab_codes(self):
        return await self.get("restrictions_lab_codes")
    
    async def set_restrictions_lab_codes(self, restrictions_lab_codes):
        await self.set("restrictions_lab_codes", restrictions_lab_codes)
    
    async def get_all_restriction_products(self):
        return await self.get("all_restriction_products")
    
    async def set_all_restriction_products(self, all_restriction_products):
        await self.set("all_restriction_products", all_restriction_products)
    
    async def get_user_recipe_preference(self):
        return await self.get("user_recipe_preference")
    
    async def set_user_recipe_preference(self, user_recipe_preference):
        await self.set("user_recipe_preference", user_recipe_preference)
    
    async def update_user_recipe_preference(self, **kwargs):
        prefs = await self.get_user_recipe_preference()
        if prefs is None:
            prefs = RecipeUserPreferencesDTO()

        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        await self.set_user_recipe_preference(prefs)
    
    async def get_get_recipe_id(self):
        return await self.get("get_recipe_id")
    
    async def set_get_recipe_id(self, recipe_id: int):
        await self.set("get_recipe_id", recipe_id)
    
    async def get_get_recipe_name(self):
        return await self.get("get_recipe_name")
    
    async def set_get_recipe_name(self, recipe_name: str):
        await self.set("get_recipe_name", recipe_name)
    
    async def delete(self):
        self._data = None
        await self.cache.delete(self.whatsapp_number)
    async def _save(self):
        await self.cache.set(self.whatsapp_number, self._data)

    async def exists(self) -> bool:
        return await self.cache.contains(self.whatsapp_number)
