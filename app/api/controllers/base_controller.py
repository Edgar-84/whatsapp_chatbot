from fastapi import APIRouter, Depends, HTTPException, Form, Request

# from src.auth.dtos.user_dtos import UserDTO, CreateUserDTO
# from src.auth.services.user_service import UserService
# from src.dependencies import UOWDep

from app.utils import MessageClient
from app.dependencies import MessageClientDep, UserStatesDep, ValidatedUsersDep, ValidClientIdsDep
from app.config.logger_settings import get_logger
from app.config.project_config import project_settings


logger = get_logger("base_controller")


router = APIRouter(tags=["Base"])

# @router.post("/create-user", response_model=UserDTO)
# async def create_user(uow: UOWDep, user_data: CreateUserDTO):
#     result: UserDTO = await UserService().create_user(
#         uow, user_data
#     )
#     return result


@router.post("/message", response_model=None)
async def reply(
    request: Request,
    message_client: MessageClientDep,    # MessageClient = Depends(get_message_client)
    user_states: UserStatesDep,    # user_states = Depends(get_user_states)
    validated_users: ValidatedUsersDep,    # validated_users = Depends(get_validated_users)
    valid_client_ids: ValidClientIdsDep,    # valid_client_ids = Depends(get_valid_client_ids)
    Body: str = Form()
):
    form_data = await request.form()
    whatsapp_number = form_data['From'].split("whatsapp:")[-1]
    user_message = Body.strip()

    if whatsapp_number not in user_states:
        user_states[whatsapp_number] = "awaiting_id"
        await message_client.send_message(
            whatsapp_number,
            "👋 Hi, your results are ready!\nPlease enter your Client ID to validate your personal chat.")
        return ""
    
    state = user_states[whatsapp_number]
    
    if state == "awaiting_id":
        if user_message in valid_client_ids:
            validated_users.add(whatsapp_number)
            user_states[whatsapp_number] = "menu"
            await message_client.send_message(
                whatsapp_number, "✅ Verification successful! Choose an option:"
            )
            await send_menu(whatsapp_number, message_client)
        else:
            await message_client.send_message(whatsapp_number, "❌ Invalid Client ID. Please try again:")
    elif state == "menu":
        await handle_main_menu(whatsapp_number, user_message, message_client)
    
    return ""

async def send_menu(whatsapp_number, message_client):
    menu_text = (
        "*Main Menu:*\n"
        "1️⃣ View My Results\n"
        "2️⃣ See My Restrictions\n"
        "3️⃣ Personalized Recipes\n"
        "4️⃣ Personal Nutrition Assistant\n"
        "0️⃣ 🔝 Main Menu"
    )
    await message_client.send_message(whatsapp_number, menu_text)

async def handle_main_menu(whatsapp_number, user_message, message_client):
    if user_message == "0":
        await send_menu(whatsapp_number)
    else:
        responses = {
            "1": "🛠 View My Results - In development...",
            "2": "🛠 See My Restrictions - In development...",
            "3": "🛠 Personalized Recipes - In development...",
            "4": "🛠 Personal Nutrition Assistant - In development...",
        }
        response = responses.get(user_message, "❌ Invalid option. Please choose from the menu:")
        await message_client.send_message(whatsapp_number, response)
        if response == "❌ Invalid option. Please choose from the menu:":
            await send_menu(whatsapp_number)
