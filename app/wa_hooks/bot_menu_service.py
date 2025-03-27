from app.wa_hooks.message_hooks import MessageClient


class BotMenuService:
    def __init__(self, message_client: MessageClient):
        self.message_client = message_client

    async def send_message(self, whatsapp_number: str, body_text: str):
        await self.message_client.send_message(whatsapp_number, body_text)

    async def send_main_menu(self, whatsapp_number: str):
        menu_text = (
            "*Main Menu:*\n"
            "1️⃣ View My Results\n"
            "2️⃣ See My Restrictions\n"
            "3️⃣ Personalized Recipes\n"
            "4️⃣ Personal Nutrition Assistant\n"
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
        
    async def send_personalized_recipes_menu(self, whatsapp_number: str):
        menu_text = (
            "🛠 Personalized Recipes - In development...\n"
            "0️⃣ 🔝 Main Menu"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)
    
    async def send_personal_nutrition_assistant_menu(self, whatsapp_number: str):
        menu_text = (
            "🛠 Personal Nutrition Assistant - In development...\n"
            "0️⃣ 🔝 Main Menu"
        )
        await self.message_client.send_message(whatsapp_number, menu_text)