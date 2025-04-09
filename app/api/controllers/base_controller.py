from fastapi import APIRouter, Depends, HTTPException, Form, Request

from app.services.ascii_service import ASCIIService
from app.dependencies import (
    BotMenuServiceDep,
    UserStatesDep,
    UOWDep,
    UserCacheDep,
    UserStates,
    AskRagForRecipeDep
)
from app.api.dtos.recipe_user_preferences_dto import RecipeUserPreferencesDTO
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
    rag_service: AskRagForRecipeDep,
    Body: str = Form()
):
    form_data = await request.form()
    whatsapp_number = form_data['From'].split("whatsapp:")[-1]
    user_message = Body.strip()

    state = user_states.get(whatsapp_number)
    # Check if user not in cache and not in verification state
    if whatsapp_number not in user_cache and state != UserStates.AWAITING_VERIFICATION:
        logger.info(f"User {whatsapp_number} not in cache and not in verification state, with message: {user_message}")
        await bot_menu_service.send_first_message(whatsapp_number)
        user_states[whatsapp_number] = UserStates.AWAITING_VERIFICATION
        return ""

    # Check if user in verification state
    if state == UserStates.AWAITING_VERIFICATION and whatsapp_number not in user_cache:
        try:
            logger.info(f"Verifying client ID for {whatsapp_number} with message: {user_message}")
            user = await UserService().get_user_by_phone_and_client_id(uow, whatsapp_number, int(user_message))
        except Exception as e:
            logger.warning(f"Error verifying client ID for {whatsapp_number}: {str(e)}")
            user = None

        if user:
            logger.info(f"User {whatsapp_number} verified successfully!")
            await bot_menu_service.send_you_verified_message(whatsapp_number)
            updated_user = await UserService().verify_user(uow, user.id)
            user_cache[whatsapp_number] = {
                "user": updated_user,
                "user_recipe_preference": None,
                "get_recipe_id": None,
                "restrictions_lab_codes": None,
                "personalized_recipes": None,
                "high_sensitivity_foods": None,
                "low_sensitivity_foods": None,
                "all_restriction_products": None
            }
            user_states[whatsapp_number] = UserStates.MAIN_MENU
            await bot_menu_service.send_main_menu(whatsapp_number)

        else:
            logger.info(f"User select Invalid Client ID {user_message} for {whatsapp_number}")
            await bot_menu_service.send_invalid_client_id_message(whatsapp_number)
        return ""

    user: UserDTO = user_cache[whatsapp_number]["user"]
    logger.info(f"User retrieved from cache: {user}")
    state = user_states.get(whatsapp_number, UserStates.AWAITING_VERIFICATION)
    logger.info(f"User state: {state}")

    # Menu for verified user
    match state:
        case UserStates.MAIN_MENU:
            match user_message:
                case "1":
                    user_states[whatsapp_number] = UserStates.MY_RESULT_MENU
                    await bot_menu_service.send_my_results_menu(whatsapp_number, user.pdf_result_link)

                case "2":
                    user_states[whatsapp_number] = UserStates.USER_WAITING_ANSWER # Set block for user message
                    await bot_menu_service.send_wait_message(whatsapp_number)
                    ascii_result_link = user.ascii_result_link

                    if user_cache[whatsapp_number]["high_sensitivity_foods"] is not None and user_cache[whatsapp_number]["low_sensitivity_foods"] is not None:
                        logger.info(f" === Find Restrictions in User cache! ===")
                        user_states[whatsapp_number] = UserStates.MY_RESTRICTIONS_MENU
                        high_sensitivity_foods_names = [food.name for food in user_cache[whatsapp_number]["high_sensitivity_foods"]]
                        low_sensitivity_foods_names = [food.name for food in user_cache[whatsapp_number]["low_sensitivity_foods"]]
                        await bot_menu_service.send_my_restrictions_menu(
                            whatsapp_number,
                            high_sensitivity_foods_names,
                            low_sensitivity_foods_names
                        )

                    elif ascii_result_link:
                        # TODO create util for work with getting restrictions info
                        file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                        logger.info(f"File ID: {file_id}")
                        high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
                        user_cache[whatsapp_number]["restrictions_lab_codes"] = high_sensitivity_foods_codes + low_sensitivity_foods_codes

                        # TODO create one request instead of two, and filter results on hight and low foods
                        high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
                        low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
                        user_cache[whatsapp_number]["high_sensitivity_foods"] = high_sensitivity_foods
                        user_cache[whatsapp_number]["low_sensitivity_foods"] = low_sensitivity_foods
                        user_cache[whatsapp_number]["all_restriction_products"] = high_sensitivity_foods + low_sensitivity_foods

                        # user_cache[whatsapp_number]["restrictions_foods_id"] = [food.id for food in high_sensitivity_foods + low_sensitivity_foods]
                        high_sensitivity_foods_names = [food.name for food in high_sensitivity_foods]
                        low_sensitivity_foods_names = [food.name for food in low_sensitivity_foods]
                        logger.info(f"High sensitivity foods: {high_sensitivity_foods_names}")
                        logger.info(f"Low sensitivity foods: {low_sensitivity_foods_names}")
                        user_states[whatsapp_number] = UserStates.MY_RESTRICTIONS_MENU
                        await bot_menu_service.send_my_restrictions_menu(whatsapp_number, high_sensitivity_foods_names, low_sensitivity_foods_names)

                    else:
                        user_states[whatsapp_number] = UserStates.MY_RESTRICTIONS_MENU
                        await bot_menu_service.send_my_restrictions_menu(whatsapp_number)

                case "3":
                    user_states[whatsapp_number] = UserStates.ASK_USER_WHANT_RECIPES
                    # Create DTO for save user preferences
                    user_cache[whatsapp_number]["user_recipe_preference"] = RecipeUserPreferencesDTO()
                    await bot_menu_service.ask_user_whant_get_recipes_menu(whatsapp_number)

                case "4" | "5":
                    await bot_menu_service.send_message(
                        whatsapp_number, "Not available yet - under development!"
                    )
                    await bot_menu_service.send_main_menu(whatsapp_number)
                    # user_states[whatsapp_number] = UserStates.NUTRITION_ASSISTANT_MENU
                    # await bot_menu_service.send_personal_nutrition_assistant_menu(whatsapp_number)
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

        case UserStates.ASK_USER_WHANT_RECIPES:
            match user_message:
                case "1":
                    user_states[whatsapp_number] = UserStates.CHOICE_MEAL_TYPE_MENU
                    await bot_menu_service.send_choice_meal_type_menu(whatsapp_number)
                case "2":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 2 to go back."
                    )

        case UserStates.CHOICE_MEAL_TYPE_MENU:
            # After client choose meal type
            match user_message:
                case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8":
                    user_states[whatsapp_number] = UserStates.DIETARY_PREFERENCE_FILTER
                    meal_type = {
                        "1": "Breakfast",
                        "2": "Lunch",
                        "3": "Dinner",
                        "4": "Snack",
                        "5": "Side Dish",
                        "6": "Salads",
                        "7": "Desserts",
                        "8": "Soups"
                    }[user_message]
                    user_cache[whatsapp_number]["user_recipe_preference"].meal_type = meal_type
                    logger.debug(f"UPDATE Meal type: {user_cache[whatsapp_number]['user_recipe_preference']}")
                    await bot_menu_service.ask_user_dietary_preference_menu(whatsapp_number)

                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back or select necessary meal type *(from 1 to 8)*."
                    )

        case UserStates.DIETARY_PREFERENCE_FILTER:
            # After client choose meal type
            match user_message:
                case "1" | "2" | "3" | "4" | "5":
                    dietary_preference = {
                        "1": "Vegetarian",
                        "2": "Vegan",
                        "3": "High Protein",
                        "4": "Low Carb",
                        "5": "No preference"
                    }[user_message]

                    user_cache[whatsapp_number]["user_recipe_preference"].dietary_preference = dietary_preference
                    logger.debug(f"UPDATE Dietary preference: {user_cache[whatsapp_number]['user_recipe_preference']}")
                    user_states[whatsapp_number] = UserStates.INCLUDE_INGREDIENTS_FILTER
                    await bot_menu_service.ask_user_include_ingredients_menu(whatsapp_number)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Select necessary Dietary preference *(from 1 to 5)*."
                    )
        
        case UserStates.INCLUDE_INGREDIENTS_FILTER:
            match user_message:
                case _:
                    await bot_menu_service.send_user_message_about_waiting_result(whatsapp_number)
                    if user_message != "0":
                        user_cache[whatsapp_number]["user_recipe_preference"].include_ingredients = user_message
                        logger.debug(f"UPDATE Include ingredients: {user_cache[whatsapp_number]['user_recipe_preference']}")
                    
                    # Add restriction products for filter
                    restrictions_products = user_cache[whatsapp_number]["all_restriction_products"]
                    if restrictions_products is None:
                        logger.debug("Restrictions not found [INCLUDE_INGREDIENTS_FILTER], processing ASCII result...")
                        ascii_result_link = user.ascii_result_link
                        if ascii_result_link:
                            file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                            logger.debug(f"File ID: {file_id}")
                            high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
                            user_cache[whatsapp_number]["restrictions_lab_codes"] = high_sensitivity_foods_codes + low_sensitivity_foods_codes
                            high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
                            low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
                            user_cache[whatsapp_number]["high_sensitivity_foods"] = high_sensitivity_foods
                            user_cache[whatsapp_number]["low_sensitivity_foods"] = low_sensitivity_foods
                            user_cache[whatsapp_number]["all_restriction_products"] = high_sensitivity_foods + low_sensitivity_foods
                            user_cache[whatsapp_number]["user_recipe_preference"].banned_foods = [food.name for food in user_cache[whatsapp_number]["all_restriction_products"]]
                            logger.debug(f"UPDATE Banned foods for user preferences: {user_cache[whatsapp_number]['user_recipe_preference']}")

                    else:
                        user_cache[whatsapp_number]["user_recipe_preference"].banned_foods = [food.name for food in restrictions_products]
                    
                    user_states[whatsapp_number] = UserStates.USER_WAITING_ANSWER

                    # Asc RAG for get recipes
                    personalized_recipe, recipe_id = await rag_service.ask_recipe(user_cache[whatsapp_number]["user_recipe_preference"])
                    logger.info(f"Catch RECIPE_ID: {recipe_id}")
                    user_states[whatsapp_number] = UserStates.SHOW_PERSONALIZED_RECIPES_MENU
                    user_cache[whatsapp_number]["get_recipe_id"] = recipe_id
                    await bot_menu_service.send_personalized_recipes_rag_menu(whatsapp_number, personalized_recipe)
                    await bot_menu_service.send_asc_quality_result_recipes_menu(whatsapp_number)

        case UserStates.USER_WAITING_ANSWER:
            # For block user message during work our logic
            match user_message:
                case _:
                    logger.debug(f" ---> User {whatsapp_number} sent message: {user_message} during waiting answer")

        case UserStates.SHOW_PERSONALIZED_RECIPES_MENU:
            match user_message:
                case "1":
                    user_states[whatsapp_number] = UserStates.MENU_SAVE_RECIPE
                    await bot_menu_service.send_menu_liked_recipe(whatsapp_number)

                case "2":
                    user_states[whatsapp_number] = UserStates.ASK_WHY_DISLIKE
                    await bot_menu_service.send_question_why_dislike(whatsapp_number)                    

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please select necessary option *(from 1 to 2)*."
                    )

        case UserStates.ASK_WHY_DISLIKE:
            match user_message:
                case _:
                    # TODO !!! Save comments and dislike recipe in DB
                    await bot_menu_service.send_message(
                        whatsapp_number, "Thanks for your comments!"
                    )
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)

        case UserStates.MENU_SAVE_RECIPE:
            match user_message:
                case "1":
                    user_states[whatsapp_number] = UserStates.SHOPPING_LIST_RECIPE_AFTER_LIKE
                    recipe_ingredients = None # TODO get from liked recipe
                    recipe_name = None # TODO get from liked recipe
                    # TODO save to shopping list table
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)
                    # await bot_menu_service.send_shopping_list_recipe_after_like(whatsapp_number, recipe_ingredients, recipe_name)

                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please select necessary option *(from 1 to 0)*."
                    )

        case UserStates.SHOPPING_LIST_RECIPE_AFTER_LIKE:
            match user_message:
                case "0":
                    user_states[whatsapp_number] = UserStates.MAIN_MENU
                    await bot_menu_service.send_main_menu(whatsapp_number)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back."
                    )

        # case UserStates.NUTRITION_ASSISTANT_MENU:
        #     match user_message:
        #         case "0":
        #             user_states[whatsapp_number] = UserStates.MAIN_MENU
        #             await bot_menu_service.send_main_menu(whatsapp_number)
        #         case _:
        #             await bot_menu_service.send_message(
        #                 whatsapp_number, "❌ Invalid option. Press 0 to go back."
        #             )

    return ""
