import asyncio

from app.wa_hooks.message_hooks import MessageClient
from app.api.dtos.recipes_dtos import RecipeDTO
from app.api.dtos.ask_recipe_dtos import AskRecipeAnswerDTO
from app.config.logger_settings import get_logger


logger = get_logger("bot_menu_service")

class BotMenuService:
    def __init__(self, message_client: MessageClient):
        self.message_client = message_client
    
    @staticmethod
    async def __format_grouped_foods_with_group(grouped_foods: list[dict[str, list[str]]]) -> str:
        lines = []
        for group in grouped_foods:
            line = f"{group['food_group_name']}:  {', '.join(group['foods'])}"
            lines.append(line)

        return "\n".join(lines)
    
    @staticmethod
    async def __format_grouped_foods(grouped_foods: list[dict[str, list[str]]]) -> str:
        lines = []
        foods = []
        for group in grouped_foods:
            foods.extend(group['foods'])
        
        for food in foods:
            line = f"{food}"
            lines.append(line)

        return "\n".join(lines)
    
    async def send_first_message(self, whatsapp_number: str):
        await self.message_client.send_message(whatsapp_number, "👋 Hi, your results are ready!\nPlease enter your Client ID to validate your personal chat.")

    async def send_message(self, whatsapp_number: str, body_text: str):
        await self.message_client.send_message(whatsapp_number, body_text)

    async def send_you_verified_message(self, whatsapp_number: str):
        await self.message_client.send_message(whatsapp_number, "✅ Your ID has been verified!")
    
    async def send_invalid_client_id_message(self, whatsapp_number: str):
        await self.message_client.send_message(whatsapp_number, "❌ Invalid Client ID. Please try again.")

    async def send_main_menu(self, whatsapp_number: str):
        menu_text = (
            "*Main Menu:*\n\n"
            "1️⃣ View My Results\n"
            "2️⃣ See My Restrictions\n"
            "3️⃣ Personalized Recipes\n"
            "4️⃣ Generate Shopping List (from liked recipes)\n"
            "5️⃣ Help / Support\n\n"
            # "0️⃣ 🔝 Main Menu"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
    

    async def send_my_results_menu(self, whatsapp_number: str, result_link: str):
        menu_text = (
            f"*View My Results*\n\n"
            f"Here is your test result PDF:\n{result_link}\n\n"
            # "0️⃣ 🔝 Main Menu"
        )   
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_my_restrictions_menu(self, whatsapp_number: str, high_sensitivity: list = None, low_sensitivity: list = None):
        if not high_sensitivity and not low_sensitivity:
            menu_text = (
                f"*See My Restrictions*\n\n"
                "No restrictions found for this user, please contact support.\n"
                # "0️⃣ 🔝 Main Menu"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)
        
        else:
            high_sensitivity_info = ", ".join([f"{r}" for r in high_sensitivity])
            low_sensitivity_info = ", ".join([f"{r}" for r in low_sensitivity])
            menu_text = (
                f"*See My Restrictions*\n\n"
                "🚫 Based on your IgG test, here are the foods you should avoid:\n"
                f"_High Sensitivity_:\n{high_sensitivity_info}\n\n"
                f"_Low Sensitivity_:\n{low_sensitivity_info}\n\n"
                # "0️⃣ 🔝 Main Menu"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_personalized_recipes_rag_menu(self, whatsapp_number: str, personalized_recipe: str = None):
        menu_text = (
            f"{personalized_recipe}\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_info_for_debug(self, whatsapp_number: str, final_answer_recipe: AskRecipeAnswerDTO):
        menu_text = (
            "*Info for analyse work LLM and RAG*\n\n"
            f"*- Recipes ID after search in RAG:*\n{final_answer_recipe.recipes_id_from_rag}\n\n"
            f"*- Filtered recipes ID after check Dicliked user recipes:*\n{final_answer_recipe.filtered_disliked_recipes_id}\n\n"
            f"*- Filtered recipes ID after check Restrictions user recipes:*\n{final_answer_recipe.filtered_restrictions_recipes_id}\n\n"
            f"*- Recipes for analyse with LLM:*\nCount: {len(final_answer_recipe.recipes_id_after_filter)}\nRecipes ID: {final_answer_recipe.recipes_id_after_filter}\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_promt_with_txt_file(self, whatsapp_number: str, link: str):
        menu_text = (
            "*Link to promt for LLM in this request*\n\n"
            f"{link}"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)


    async def send_asc_quality_result_recipes_menu(self, whatsapp_number: str):
        """
        Send message to user about select Like or Dislike recipe
        """

        menu_text = (
            "*What would you like to do?*\n\n"
            "1️⃣ Like Recipe\n"
            "2️⃣ Dislike Recipe\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    # async def send_personalized_recipes_menu(self, whatsapp_number: str, recipes: list[RecipeDTO] = None):
    #     if not recipes:
    #         menu_text = (
    #             f"*Personalized Recipes*\n"
    #             "No personalized recipes found for this user, please contact support.\n"
    #             "0️⃣ 🔝 Main Menu"
    #         )
    #         await self.message_client.send_message(whatsapp_number, menu_text)
        
    #     else:
    #         # menu_text = (
    #         #     f"*Personalized Recipes*\n"
    #         #     f"{', '.join(recipes)}\n\n"
    #         #     "0️⃣ 🔝 Main Menu"
    #         # )
    #         menu_text = "*Personalized Recipes*\n"
    #         if len(recipes) > 0:

    #             for index, recipe in enumerate(recipes, 1):
    #                 menu_text += f"{index}. {recipe.name}\n"
    #                 if recipe.sub_title:
    #                     menu_text += f"{recipe.sub_title}\n\n"
    #                 else:
    #                     menu_text += "\n"
    #         else:
    #             menu_text += "No personalized recipes found!\n"

    #         menu_text += "0️⃣ 🔝 Main Menu"
    #         await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_personal_nutrition_assistant_menu(self, whatsapp_number: str):
        menu_text = (
            "🛠 Personal Nutrition Assistant - In development...\n"
            "0️⃣ 🔝 Main Menu"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_choice_meal_type_menu(self, whatsapp_number: str):
        # TODO maybe change on dynamic menu with 'meal_type' table
        menu_text = (
            "*What type of meal are you looking for?*\n\n"
            "1️⃣ Breakfast\n"
            "2️⃣ Lunch\n"
            "3️⃣ Dinner\n"
            "4️⃣ Snack\n"
            "5️⃣ Side Dish\n"
            "6️⃣ Salads\n"
            "7️⃣ Desserts\n"
            "8️⃣ Soups\n\n"
            "0️⃣ 🔝 Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def ask_user_whant_get_recipes_menu(self, whatsapp_number: str):
        menu_text = (
            "*Would you like to get recipe suggestions based on your results?*\n\n"
            "1️⃣ Yes, show me recipes\n"
            "0️⃣ 🔝 No, return to Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def ask_user_dietary_preference_menu(self, whatsapp_number: str):
        menu_text = (
            "*Do you have any dietary preferences for this meal*\n\n"
            "1️⃣ Vegetarian\n"
            "2️⃣ Vegan\n"
            "3️⃣ High Protein\n"
            "4️⃣ Low Carb\n"
            "5️⃣ No preference\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def ask_user_include_ingredients_menu(self, whatsapp_number: str):
        menu_text = (
            "*Would you like to include any ingredients you already have at home?*\n"
            "_(Example: rice, spinach, tuna)_\n"
            "Reply with a list of ingredients, or reply *'0' to skip.*\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_user_message_about_waiting_result(self, whatsapp_number: str):
        """
        Send message to user about waiting for result and preparing recipes
        """

        menu_text = (
            "Thank you for your clarifications!\n"
            "Please wait a little while, we are preparing suitable recipes...\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_wait_message(self, whatsapp_number: str):
        """
        Send message to user about waiting for long answer results
        """

        menu_text = (
            "Please wait a little while, we are preparing results...\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_question_why_dislike(self, whatsapp_number: str):
        menu_text = (
            "Thanks for your review!\n"
            "Could you please describe why you disliked this recipe so that we can pick\n"
            "the most appropriate ones for you in the future\n\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    
    async def send_menu_liked_recipe(self, whatsapp_number: str):
        menu_text = (
            "*Thanks for your review!*\n"
            "*What would you like to do?*\n\n"
            "1️⃣ Generate Shopping List for Recipe\n"
            "0️⃣ 🔝 Back to Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_shopping_list_recipe_after_like(self, whatsapp_number: str, recipe_ingredients: str, recipe_name: str):
        recipe_ingredients = await self.__format_grouped_foods(recipe_ingredients)
        menu_text = (
            f"🛒Here’s your shopping list for *{recipe_name}*\n\n"
            f"{recipe_ingredients}\n\n"
            # "0️⃣ 🔝 Back to Main Menu\n"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
