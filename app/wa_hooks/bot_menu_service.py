from app.wa_hooks.message_hooks import MessageClient
from app.api.dtos.recipes_dtos import RecipeDTO


class BotMenuService:
    def __init__(self, message_client: MessageClient):
        self.message_client = message_client

    async def send_message(self, whatsapp_number: str, body_text: str):
        await self.message_client.send_message(whatsapp_number, body_text)

    async def send_main_menu(self, whatsapp_number: str):
        menu_text = (
            "*Main Menu:*\n\n"
            "1️⃣ View My Results\n"
            "2️⃣ See My Restrictions\n"
            "3️⃣ Personalized Recipes\n"
            "4️⃣ Personal Nutrition Assistant\n\n"
            "0️⃣ 🔝 Main Menu"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
    

    async def send_my_results_menu(self, whatsapp_number: str, result_link: str):
        menu_text = (
            f"View My Results\n"
            f"{result_link}\n"
            "0️⃣ 🔝 Main Menu"
        )   
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_my_restrictions_menu(self, whatsapp_number: str, high_sensitivity: list = None, low_sensitivity: list = None):
        if not high_sensitivity and not low_sensitivity:
            menu_text = (
                f"*See My Restrictions*\n"
                "No restrictions found for this user, please contact support.\n"
                "0️⃣ 🔝 Main Menu"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)
        
        else:
            high_sensitivity_info = ", ".join([f"{r}" for r in high_sensitivity])
            low_sensitivity_info = ", ".join([f"{r}" for r in low_sensitivity])
            menu_text = (
                f"*See My Restrictions*\n"
                f"_High Sensitivity_:\n{high_sensitivity_info}\n\n"
                f"_Low Sensitivity_:\n{low_sensitivity_info}\n\n"
                "0️⃣ 🔝 Main Menu"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)
        
    async def send_personalized_recipes_menu(self, whatsapp_number: str, recipes: list[RecipeDTO] = None):
        if not recipes:
            menu_text = (
                f"*Personalized Recipes*\n"
                "No personalized recipes found for this user, please contact support.\n"
                "0️⃣ 🔝 Main Menu"
            )
            await self.message_client.send_message(whatsapp_number, menu_text)
        
        else:
            # menu_text = (
            #     f"*Personalized Recipes*\n"
            #     f"{', '.join(recipes)}\n\n"
            #     "0️⃣ 🔝 Main Menu"
            # )
            menu_text = "*Personalized Recipes*\n"
            if len(recipes) > 0:

                for index, recipe in enumerate(recipes, 1):
                    menu_text += f"{index}. {recipe.name}\n"
                    if recipe.sub_title:
                        menu_text += f"{recipe.sub_title}\n\n"
                    else:
                        menu_text += "\n"
            else:
                menu_text += "No personalized recipes found!\n"

            menu_text += "0️⃣ 🔝 Main Menu"
            await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_personal_nutrition_assistant_menu(self, whatsapp_number: str):
        menu_text = (
            "🛠 Personal Nutrition Assistant - In development...\n"
            "0️⃣ 🔝 Main Menu"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)

    async def send_choice_meal_type_menu(self, whatsapp_number: str):
        # TODO maybe change on dynamic menu with 'meal_type' table
        menu_text = (
            "*Choose Meal Type*\n\n"
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
