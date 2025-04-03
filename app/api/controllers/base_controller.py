from fastapi import APIRouter, Depends, HTTPException, Form, Request

from app.services.ascii_service import ASCIIService
from app.dependencies import (
    BotMenuServiceDep,
    UserStatesDep,
    UOWDep,
    UserCacheDep,
    UserStates
)
from app.api.dtos.user_dtos import UserDTO
from app.api.dtos.food_dtos import FoodDTO
from app.api.dtos.recipes_dtos import RecipeDTO
from app.api.services.user_service import UserService
from app.api.services.food_service import FoodService
from app.api.services.recipes_service import RecipesService
from app.config.logger_settings import get_logger


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
            # TODO CASH model for User ! Add class for work with cash and log every get\add operation (include phone number for debugging)
            user_cache[whatsapp_number] = {
                "user": user,
                "restrictions_lab_codes": None,
                "restrictions_foods_id": None,
                "personalized_recipes": None
            }
            logger.info(f"Save user with ClientID: {user.client_id} in cache")
        else:
            logger.info(f"User with ClientID: {user_message} not found! WhatsApp number: {whatsapp_number}")
            await bot_menu_service.send_message(
                whatsapp_number,
                "👋 Hi, your results are ready!\nPlease enter your Client ID to validate your personal chat."
            )
            return ""

    user: UserDTO = user_cache[whatsapp_number]["user"]
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
                user_cache[whatsapp_number]["user"] = updated_user
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
                    ascii_result_link = user.ascii_result_link

                    if ascii_result_link:
                        file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                        logger.info(f"File ID: {file_id}")
                        high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
                        user_cache[whatsapp_number]["restrictions_lab_codes"] = high_sensitivity_foods_codes + low_sensitivity_foods_codes

                        # TODO create one request instead of two, and filter results on hight and low foods
                        high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
                        low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
                        user_cache[whatsapp_number]["restrictions_foods_id"] = [food.id for food in high_sensitivity_foods + low_sensitivity_foods]
                        high_sensitivity_foods = [food.name for food in high_sensitivity_foods]
                        low_sensitivity_foods = [food.name for food in low_sensitivity_foods]
                        logger.info(f"High sensitivity foods: {high_sensitivity_foods}")
                        logger.info(f"Low sensitivity foods: {low_sensitivity_foods}")
                        await bot_menu_service.send_my_restrictions_menu(whatsapp_number, high_sensitivity_foods, low_sensitivity_foods)
                    else:
                        await bot_menu_service.send_my_restrictions_menu(whatsapp_number)
                case "3":
                    user_states[whatsapp_number] = UserStates.PERSONALIZED_RECIPES_MENU
                    await bot_menu_service.send_choice_meal_type_menu(whatsapp_number)
                    # # Logic for work with recipes
                    # restrictions_products = user_cache[whatsapp_number].get("restrictions")
                    # if restrictions_products is None:
                    #     ascii_result_link = user.ascii_result_link
                    #     if ascii_result_link:
                    #         file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                    #         logger.info(f"File ID: {file_id}")
                    #         high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
                    #         user_cache[whatsapp_number]["restrictions"] = high_sensitivity_foods_codes + low_sensitivity_foods_codes
                    #         restrictions_products = user_cache[whatsapp_number]["restrictions"]
                    #     else:
                    #         await bot_menu_service.send_personalized_recipes_menu(whatsapp_number)

                    # recipes = []
                    # # TODO create logic for get recipes       
                    # await bot_menu_service.send_personalized_recipes_menu(whatsapp_number, recipes)
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
            # After client choose meal type
            match user_message:
                case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8":
                    user_states[whatsapp_number] = UserStates.CHOICE_MEAL_TYPE_MENU
                    meal_type = {
                        "1": 4,
                        "2": 5,
                        "3": 6,
                        "4": 7,
                        "5": 9,
                        "6": 10,
                        "7": 11,
                        "8": 12
                    }[user_message]
                    
                    # Logic for work with recipes
                    restrictions_products = user_cache[whatsapp_number].get("restrictions_foods_id")
                    if restrictions_products is None:
                        logger.info("Restrictions not found [PERSONALIZED_RECIPES_MENU], processing ASCII result...")
                        ascii_result_link = user.ascii_result_link
                        if ascii_result_link:
                            file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                            logger.info(f"File ID: {file_id}")
                            high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
                            logger.info(f"High sensitivity foods: {high_sensitivity_foods_codes}")
                            logger.info(f"Low sensitivity foods: {low_sensitivity_foods_codes}")
                            user_cache[whatsapp_number]["restrictions_lab_codes"] = high_sensitivity_foods_codes + low_sensitivity_foods_codes
                            # Get foods by lab codes
                            restriction_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, user_cache[whatsapp_number]["restrictions_lab_codes"])
                            user_cache[whatsapp_number]["restrictions_foods_id"] = [food.id for food in restriction_foods]
                            restrictions_products = user_cache[whatsapp_number]["restrictions_foods_id"]
                            
                        else:
                            await bot_menu_service.send_personalized_recipes_menu(whatsapp_number)

                    recipes: list[RecipeDTO] = await RecipesService().get_recipes_without_forbidden_foods(
                        uow=uow,
                        meal_type_id=meal_type,
                        forbidden_foods=restrictions_products
                    )
                    user_cache[whatsapp_number]["personalized_recipes"] = {numb: recipe for numb, recipe in enumerate(recipes, 1)}
                    added_recipes = [(numb, recipe.id) for numb, recipe in user_cache[whatsapp_number]["personalized_recipes"].items()]
                    logger.info(f"Personalized recipes added in CASH: {added_recipes}")

                    await bot_menu_service.send_personalized_recipes_menu(whatsapp_number, recipes)

                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back."
                    )

        case UserStates.CHOICE_MEAL_TYPE_MENU:
            # After client choose meal type and we return recipes
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
