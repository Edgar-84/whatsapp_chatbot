from fastapi import APIRouter, Depends, HTTPException, Form, Request

# from src.auth.dtos.user_dtos import UserDTO, CreateUserDTO
# from src.auth.services.user_service import UserService
# from src.dependencies import UOWDep


from app.dependencies import (
    BotMenuServiceDep,
    UserStatesDep,
    UOWDep,
    UserCacheDep,
    UserStates
)
from app.api.dtos.user_dtos import UserDTO
from app.api.services.user_service import UserService
from app.config.logger_settings import get_logger
from app.config.project_config import project_settings


logger = get_logger("base_controller")


router = APIRouter(tags=["Base"])


@router.post("/message", response_model=None)
async def reply(
    request: Request,
    uow: UOWDep,
    bot_menu_service: BotMenuServiceDep,
    user_states: UserStatesDep,
    user_cache: UserCacheDep,
    Body: str = Form()
):
    form_data = await request.form()
    whatsapp_number = form_data['From'].split("whatsapp:")[-1]
    user_message = Body.strip()

    if whatsapp_number not in user_cache:
        try:
            user = await UserService().get_user_by_phone_and_client_id(uow, whatsapp_number, int(user_message))
        except Exception as e:
            logger.warning(f"Mistake during check user with phone: {whatsapp_number} - {str(e)}")
            user = None

        if user:
            user_cache[whatsapp_number] = user
            logger.info(f"Save user with ClientID: {user.client_id} in cache")
        else:
            logger.info(f"User with ClientID: {user_message} not found! WhatsApp number: {whatsapp_number}")
            await bot_menu_service.send_message(
                whatsapp_number,
                "👋 Hi, your results are ready!\nPlease enter your Client ID to validate your personal chat."
            )
            return ""

    user: UserDTO = user_cache[whatsapp_number]
    logger.info(f"User retrieved from cache: {user}")
    state = user_states.get(whatsapp_number, UserStates.AWAITING_VERIFICATION)
    logger.info(f"User state: {state}")

    match state:
        case UserStates.AWAITING_VERIFICATION:
            if user.verified:
                user_states[whatsapp_number] = UserStates.MAIN_MENU
                await bot_menu_service.send_main_menu(whatsapp_number)

            elif user_message == user.client_id and user.phone == whatsapp_number:
                updated_user = await UserService().verify_user(uow, user.id)
                user_cache[whatsapp_number] = updated_user
                user_states[whatsapp_number] = UserStates.MAIN_MENU
                await bot_menu_service.send_message(
                    whatsapp_number, "✅ Verification successful! Choose an option:"
                )
                await bot_menu_service.send_main_menu(whatsapp_number)
            else:
                await bot_menu_service.send_message(
                    whatsapp_number, "❌ Invalid Client ID. Please try again:"
                )

        case UserStates.MAIN_MENU:
            match user_message:
                case "1":
                    user_states[whatsapp_number] = UserStates.MY_RESULT_MENU
                    await bot_menu_service.send_my_results_menu(whatsapp_number, user.pdf_result_link)
                case "2":
                    user_states[whatsapp_number] = UserStates.MY_RESTRICTIONS_MENU
                    await bot_menu_service.send_my_restrictions_menu(whatsapp_number)
                case "3":
                    user_states[whatsapp_number] = UserStates.PERSONALIZED_RECIPES_MENU
                    await bot_menu_service.send_personalized_recipes_menu(whatsapp_number)
                case "4":
                    user_states[whatsapp_number] = UserStates.NUTRITION_ASSISTANT_MENU
                    await bot_menu_service.send_personal_nutrition_assistant_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose from the menu:"
                    )
                    await bot_menu_service.send_main_menu(whatsapp_number)

        case UserStates.MY_RESULT_MENU:
            match user_message:
                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back."
                    )

        case UserStates.MY_RESTRICTIONS_MENU:
            match user_message:
                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back."
                    )

        case UserStates.PERSONALIZED_RECIPES_MENU:
            match user_message:
                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back."
                    )

        case UserStates.NUTRITION_ASSISTANT_MENU:
            match user_message:
                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back."
                    )

    return ""
