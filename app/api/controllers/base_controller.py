import asyncio
from fastapi import APIRouter, Depends, HTTPException, Form, Request

from app.utils.cache.user_session import UserSession, UserStates
from app.services.ascii_service import ASCIIService
from app.services.google_upload_file_service import GoogleDriveService
from app.dependencies import (
    BotMenuServiceDep,
    UserStatesDep,
    UOWDep,
    UserCacheDep,
    AskRagForRecipeDep,
    GoogleDriveServiceDep
)
from app.api.dtos.recipe_user_preferences_dto import RecipeUserPreferencesDTO
from app.api.dtos.user_dtos import UserDTO
from app.api.dtos.food_dtos import FoodDTO
from app.api.dtos.recipe_ratings_dtos import CreateRecipeRatingDTO
from app.api.dtos.shopping_list_dtos import CreateShoppingListDTO, ShoppingListDTO
# from app.api.dtos.recipes_dtos import RecipeDTO

from app.api.services.user_service import UserService
from app.api.services.food_service import FoodService
from app.api.services.shopping_list_service import ShoppingListService
# from app.api.services.recipes_service import RecipesService
from app.api.services.recipe_ratings_service import RecipeRatingsService
from app.config.logger_settings import get_logger


logger = get_logger("base_controller")


router = APIRouter(tags=["Base"])


@router.post("/message", response_model=None)
async def reply(
    request: Request,
    uow: UOWDep,
    bot_menu_service: BotMenuServiceDep,
    user_cache: UserCacheDep,
    rag_service: AskRagForRecipeDep,
    google_drive_service: GoogleDriveServiceDep,
    Body: str = Form()
):
    form_data = await request.form()
    whatsapp_number = form_data['From'].split("whatsapp:")[-1]
    user_message = Body.strip()

    user_session = UserSession(user_cache, whatsapp_number)

    if not await user_session.exists():
        logger.info(f"User {whatsapp_number} not in cache. Checking DB verification status.")
        try:
            user = await UserService().get_user_by_phone(uow, whatsapp_number)
            if user is None:
                logger.info(f"Failed to get user by phone {whatsapp_number}: {e}")
                await bot_menu_service.send_message(whatsapp_number, "Your number is not in the system, contact support at @support email")
                return ""

        except Exception as e:
            logger.warning(f"Failed to get user by phone {whatsapp_number}: {e}")
            await bot_menu_service.send_message(whatsapp_number, "Your number is not in the system, contact support at @support email")
            return ""

        if user.verified:
            logger.info(f"User {whatsapp_number} is already verified in DB.")
            await user_session.set_user(user)
            await user_session.set_state(UserStates.MAIN_MENU)
            await bot_menu_service.send_main_menu(whatsapp_number)
            return ""

        else:
            logger.info(f"User {whatsapp_number} is not verified. Sending first message.")
            await user_session.set_user(user)
            await user_session.set_state(UserStates.AWAITING_VERIFICATION)
            await bot_menu_service.send_first_message(whatsapp_number)
            return ""

    state = await user_session.get_state()
    logger.info(f"USER STATE: {state}")
    user: UserDTO = await user_session.get_user()
    logger.info(f"USER: {user}")

    if state == UserStates.AWAITING_VERIFICATION:
        try:
            logger.info(f"Trying to verify {whatsapp_number} with Client ID: {user_message}")
            verified_user = await UserService().get_user_by_phone_and_client_id(uow, whatsapp_number, int(user_message))
            if verified_user is None:
                raise Exception("Verification failed")
        except Exception as e:
            logger.warning(f"Verification error for {whatsapp_number}: {e}")
            await bot_menu_service.send_invalid_client_id_message(whatsapp_number)
            return ""

        logger.info(f"User {whatsapp_number} verified successfully.")
        updated_user = await UserService().verify_user(uow, verified_user.id)
        await user_session.set_user(updated_user)
        await user_session.set_state(UserStates.MAIN_MENU)
        await bot_menu_service.send_you_verified_message(whatsapp_number)
        await bot_menu_service.send_main_menu(whatsapp_number)
        return ""


    # Menu for verified user
    match state:
        case UserStates.MAIN_MENU:
            match user_message:
                case "1":
                    await bot_menu_service.send_my_results_menu(whatsapp_number, user.pdf_result_link)
                    # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu(whatsapp_number)
                    return ""
                case "2":
                    # await user_states.set(whatsapp_number, UserStates.USER_WAITING_ANSWER) # Set block for user message
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    await bot_menu_service.send_wait_message(whatsapp_number)
                    ascii_result_link = user.ascii_result_link

                    high_sensitivity_foods = await user_session.get_high_sensitivity_foods()
                    low_sensitivity_foods = await user_session.get_low_sensitivity_foods()

                    if high_sensitivity_foods is not None and low_sensitivity_foods is not None:
                        logger.info(f" === Find Restrictions in User cache! ===")
                        # user_states[whatsapp_number] = UserStates.MY_RESTRICTIONS_MENU
                        high_sensitivity_foods_names = [food.name for food in high_sensitivity_foods]
                        low_sensitivity_foods_names = [food.name for food in low_sensitivity_foods]
                        await bot_menu_service.send_my_restrictions_menu(
                            whatsapp_number,
                            high_sensitivity_foods_names,
                            low_sensitivity_foods_names
                        )
                        # await user_session.set(whatsapp_number, UserStates.MAIN_MENU)
                        await user_session.set_state(UserStates.MAIN_MENU)
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_main_menu(whatsapp_number)

                    elif ascii_result_link:
                        # TODO create util for work with getting restrictions info
                        file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                        logger.info(f"File ID: {file_id}")
                        high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
                        # user_cache[whatsapp_number]["restrictions_lab_codes"] = high_sensitivity_foods_codes + low_sensitivity_foods_codes
                        await user_session.set_restrictions_lab_codes(high_sensitivity_foods_codes + low_sensitivity_foods_codes)
                        # TODO create one request instead of two, and filter results on hight and low foods
                        high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
                        low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
                        # user_cache[whatsapp_number]["high_sensitivity_foods"] = high_sensitivity_foods
                        # user_cache[whatsapp_number]["low_sensitivity_foods"] = low_sensitivity_foods
                        # user_cache[whatsapp_number]["all_restriction_products"] = high_sensitivity_foods + low_sensitivity_foods
                        await user_session.set_high_sensitivity_foods(high_sensitivity_foods)
                        await user_session.set_low_sensitivity_foods(low_sensitivity_foods)
                        await user_session.set_all_restriction_products(high_sensitivity_foods + low_sensitivity_foods)

                        # user_cache[whatsapp_number]["restrictions_foods_id"] = [food.id for food in high_sensitivity_foods + low_sensitivity_foods]
                        high_sensitivity_foods_names = [food.name for food in high_sensitivity_foods]
                        low_sensitivity_foods_names = [food.name for food in low_sensitivity_foods]
                        logger.info(f"High sensitivity foods: {high_sensitivity_foods_names}")
                        logger.info(f"Low sensitivity foods: {low_sensitivity_foods_names}")
                        # user_states[whatsapp_number] = UserStates.MY_RESTRICTIONS_MENU
                        await bot_menu_service.send_my_restrictions_menu(whatsapp_number, high_sensitivity_foods_names, low_sensitivity_foods_names)
                        # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                        await user_session.set_state(UserStates.MAIN_MENU)
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_main_menu(whatsapp_number)

                    else:
                        # user_states[whatsapp_number] = UserStates.MY_RESTRICTIONS_MENU
                        await bot_menu_service.send_my_restrictions_menu(whatsapp_number)
                        # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                        await user_session.set_state(UserStates.MAIN_MENU)
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_main_menu(whatsapp_number)

                case "3":
                    # await user_states.set(whatsapp_number, UserStates.CHOICE_MEAL_TYPE_MENU)
                    await user_session.set_state(UserStates.CHOICE_MEAL_TYPE_MENU)
                    # Create DTO for save user preferences
                    # user_cache[whatsapp_number]["user_recipe_preference"] = RecipeUserPreferencesDTO()
                    await user_session.set_user_recipe_preference(RecipeUserPreferencesDTO())
                    await bot_menu_service.send_choice_meal_type_menu(whatsapp_number)
                    # await bot_menu_service.ask_user_whant_get_recipes_menu(whatsapp_number)
                case "4":
                    # await user_states.set(whatsapp_number, UserStates.USER_WAITING_ANSWER) # Set block for user message
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    get_user_shopping_list = await ShoppingListService.get_user_shopping_lists(uow, user.id)
                    if len(get_user_shopping_list) == 0:
                        await bot_menu_service.send_message(whatsapp_number, "*You have no liked recipes in your shopping list!*")
                    
                    else:
                        await bot_menu_service.send_message(whatsapp_number, "*Your shopping list for your liked recipes:*\n")
                        await asyncio.sleep(0.5)
                        grouped_foods_tasks = [
                            FoodService.get_grouped_foods_by_recipe_id(uow, shopping_list.recipe_id)
                            for shopping_list in get_user_shopping_list
                        ]
                        grouped_foods_results = await asyncio.gather(*grouped_foods_tasks)
                        for shopping_list, grouped_foods in zip(get_user_shopping_list, grouped_foods_results):
                            await bot_menu_service.send_shopping_list_recipe_after_like(
                                whatsapp_number,
                                grouped_foods,
                                shopping_list.recipe_name
                            )
                            await asyncio.sleep(1)
                    
                    # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu(whatsapp_number)
                
                case "5":
                    await bot_menu_service.send_message(
                        whatsapp_number, "Not available yet - under development!"
                    )
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu(whatsapp_number)
                    # user_states[whatsapp_number] = UserStates.NUTRITION_ASSISTANT_MENU
                    # await bot_menu_service.send_personal_nutrition_assistant_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please choose from the menu:"
                    )
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu(whatsapp_number)

        case UserStates.ASK_USER_WHANT_RECIPES:
            # TODO can be deleted, old menu
            match user_message:
                case "1":
                    # await user_states.set(whatsapp_number, UserStates.CHOICE_MEAL_TYPE_MENU)
                    await user_session.set_state(UserStates.CHOICE_MEAL_TYPE_MENU)
                    await bot_menu_service.send_choice_meal_type_menu(whatsapp_number)
                case "0":
                    # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Press 0 to go back."
                    )

        case UserStates.CHOICE_MEAL_TYPE_MENU:
            # After client choose meal type
            match user_message:
                case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8":
                    # await user_states.set(whatsapp_number, UserStates.DIETARY_PREFERENCE_FILTER)
                    await user_session.set_state(UserStates.DIETARY_PREFERENCE_FILTER)
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
                    # user_cache[whatsapp_number]["user_recipe_preference"].meal_type = meal_type
                    await user_session.update_user_recipe_preference(meal_type=meal_type)
                    await bot_menu_service.ask_user_dietary_preference_menu(whatsapp_number)
                case "0":
                    # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                    await user_session.set_state(UserStates.MAIN_MENU)
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
                    
                    # user_cache[whatsapp_number]["user_recipe_preference"].dietary_preference = dietary_preference
                    await user_session.update_user_recipe_preference(dietary_preference=dietary_preference)
                    dietary_preference = await user_session.get_user_recipe_preference()
                    logger.debug(f"UPDATE Dietary preference: {dietary_preference}")
                    # await user_states.set(whatsapp_number, UserStates.INCLUDE_INGREDIENTS_FILTER)
                    await user_session.set_state(UserStates.INCLUDE_INGREDIENTS_FILTER)
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
                        # user_cache[whatsapp_number]["user_recipe_preference"].include_ingredients = user_message
                        await user_session.update_user_recipe_preference(include_ingredients=user_message)
                    
                    # Add restriction products for filter
                    # restrictions_products = user_cache[whatsapp_number]["all_restriction_products"]
                    restrictions_products = await user_session.get_all_restriction_products()
                    if restrictions_products is None:
                        logger.debug("Restrictions not found [INCLUDE_INGREDIENTS_FILTER], processing ASCII result...")
                        ascii_result_link = user.ascii_result_link
                        if ascii_result_link:
                            file_id = ascii_result_link.split("/d/")[1].split("/view")[0]
                            logger.debug(f"File ID: {file_id}")
                            high_sensitivity_foods_codes, low_sensitivity_foods_codes = await ASCIIService.process_csv(file_id)
                            # user_cache[whatsapp_number]["restrictions_lab_codes"] = high_sensitivity_foods_codes + low_sensitivity_foods_codes
                            await user_session.set_restrictions_lab_codes(high_sensitivity_foods_codes + low_sensitivity_foods_codes)
                            high_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, high_sensitivity_foods_codes)
                            low_sensitivity_foods: list[FoodDTO] = await FoodService().get_foods_by_list_lab_codes(uow, low_sensitivity_foods_codes)
                            # user_cache[whatsapp_number]["high_sensitivity_foods"] = high_sensitivity_foods
                            # user_cache[whatsapp_number]["low_sensitivity_foods"] = low_sensitivity_foods
                            # user_cache[whatsapp_number]["all_restriction_products"] = high_sensitivity_foods + low_sensitivity_foods
                            await user_session.set_high_sensitivity_foods(high_sensitivity_foods)
                            await user_session.set_low_sensitivity_foods(low_sensitivity_foods)
                            await user_session.set_all_restriction_products(high_sensitivity_foods + low_sensitivity_foods)
                            # user_cache[whatsapp_number]["user_recipe_preference"].banned_foods = [food.name for food in user_cache[whatsapp_number]["all_restriction_products"]]
                            all_restr_products = await user_session.get_all_restriction_products()
                            await user_session.update_user_recipe_preference(banned_foods=[food.name for food in all_restr_products])
                        
                    else:
                        # user_cache[whatsapp_number]["user_recipe_preference"].banned_foods = [food.name for food in restrictions_products]
                        await user_session.update_user_recipe_preference(banned_foods=[food.name for food in restrictions_products])
                    
                    # await user_states.set(whatsapp_number, UserStates.USER_WAITING_ANSWER)
                    await user_session.set_state(UserStates.USER_WAITING_ANSWER)
                    
                    # Get disliked recipes
                    disliked_recipes_list = await RecipeRatingsService.get_disliked_recipes_by_user_id(uow, user.id)
                    disliked_recipes_id = [recipe.recipe_id for recipe in disliked_recipes_list]
                    disliked_recipes_comments = [recipe.comment for recipe in disliked_recipes_list if recipe.comment is not None]
                    logger.info(f"Disliked recipes list: {disliked_recipes_list} for user: {user.id}")
                    logger.info(f"Disliked recipes comments: {disliked_recipes_comments} for user: {user.id}")
                    # user_cache[whatsapp_number]["user_recipe_preference"].disliked_recipes_id = disliked_recipes_id
                    # user_cache[whatsapp_number]["user_recipe_preference"].disliked_recipes_comments = disliked_recipes_comments
                    await user_session.update_user_recipe_preference(disliked_recipes_id=disliked_recipes_id, disliked_recipes_comments=disliked_recipes_comments)
                    
                    # Asc RAG for get recipes
                    user_recipe_preference = await user_session.get_user_recipe_preference()
                    # personalized_recipe, recipe_id, recipe_name = await rag_service.ask_recipe(user_recipe_preference) #user_cache[whatsapp_number]["user_recipe_preference"])
                    final_answer_recipe = await rag_service.ask_recipe(user_recipe_preference)
                    logger.info(f"Catch RECIPE_ID and update in cash: {final_answer_recipe.ai_result_recipe_id}")
                    # await user_states.set(whatsapp_number, UserStates.SHOW_PERSONALIZED_RECIPES_MENU)
                    await user_session.set_state(UserStates.SHOW_PERSONALIZED_RECIPES_MENU)
                    await user_session.set_get_recipe_id(int(final_answer_recipe.ai_result_recipe_id))
                    await user_session.set_get_recipe_name(final_answer_recipe.ai_result_recipe_name)
                    logger.info(f"Before filter: {final_answer_recipe.recipes_after_filter}")
                    logger.info(f"ID for selected: {final_answer_recipe.ai_result_recipe_id}")
                    filtered_selected = [recipe for recipe in final_answer_recipe.recipes_after_filter if recipe["id"] != int(final_answer_recipe.ai_result_recipe_id)]
                    await user_session.set_recipes_list_for_llm_research(filtered_selected)
                    await user_session.set_llm_recipe_index(0)

                    # TODO for test
                    info_about_all_recipes = await user_session.get_recipes_list_for_llm_research()
                    logger.debug(f"Info about all recipes [filtered]: {info_about_all_recipes}")
                    
                    # ai_recommendation, selected_recipe = personalized_recipe
                    await bot_menu_service.send_personalized_recipes_rag_menu(whatsapp_number, final_answer_recipe.ai_result_recomendation)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_personalized_recipes_rag_menu(whatsapp_number, final_answer_recipe.ai_result_recipe_details)
                    await asyncio.sleep(1.5)

                    # TODO INFO for Debug work LLM and RAG
                    await bot_menu_service.send_info_for_debug(whatsapp_number, final_answer_recipe)
                    await asyncio.sleep(0.5)

                    prompt_link = await google_drive_service.upload_text_file(
                        filename="prompt",
                        content=final_answer_recipe.prompt_for_llm,
                        delete_after_upload=False
                    )

                    logger.info(f"Prepare Link to prompt for LLM: {prompt_link}\nFor client: {whatsapp_number}")
                    await bot_menu_service.send_promt_with_txt_file(whatsapp_number, prompt_link)
                    # await bot_menu_service.send_prompt_in_two_parts(whatsapp_number, final_answer_recipe.prompt_for_llm)
                    # TODO END Debug part
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_asc_quality_result_recipes_menu(whatsapp_number)

        case UserStates.USER_WAITING_ANSWER:
            # For block user message during work our logic
            match user_message:
                case _:
                    logger.debug(f" ---> User {whatsapp_number} sent message: {user_message} during waiting answer")

        case UserStates.SHOW_PERSONALIZED_RECIPES_MENU:
            match user_message:
                case "1":
                    # await user_states.set(whatsapp_number, UserStates.MENU_SAVE_RECIPE)
                    await user_session.set_state(UserStates.MENU_SAVE_RECIPE)
                    # Save liked recipe
                    await bot_menu_service.send_menu_liked_recipe(whatsapp_number)
                    get_recipe_id = await user_session.get_get_recipe_id()
                    rating_dto = CreateRecipeRatingDTO(
                        user_id=user.id,
                        recipe_id=get_recipe_id,
                        rating=5,
                    )
                    await RecipeRatingsService.create_recipe_rating(uow, rating_dto)
                    get_recipe_name = await user_session.get_get_recipe_name()
                    # Create Shopping List
                    shopping_list_dto = CreateShoppingListDTO(
                        user_id=user.id,
                        recipe_id=get_recipe_id,
                        recipe_name=get_recipe_name
                    )
                    await ShoppingListService.create_shopping_list(uow, shopping_list_dto)

                case "2":
                    # await user_states.set(whatsapp_number, UserStates.ASK_WHY_DISLIKE)
                    await user_session.set_state(UserStates.ASK_WHY_DISLIKE)
                    await bot_menu_service.send_question_why_dislike(whatsapp_number)

                case "3":
                    next_llm_recipe = await user_session.get_next_llm_recipe()
                    logger.info(f"Next LLM Recipe: {next_llm_recipe}")
                    if not next_llm_recipe:
                        await bot_menu_service.send_message(whatsapp_number, "You have viewed all available recipes under your previous request!")
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_asc_quality_result_recipes_menu_without_3(whatsapp_number)
                    
                    else:
                        recipe_info = await rag_service.get_recipe_info_message(recipe=next_llm_recipe)
                        await bot_menu_service.send_message(whatsapp_number, recipe_info)
                        await asyncio.sleep(1.5)
                        await bot_menu_service.send_asc_quality_result_recipes_menu(whatsapp_number)

                case "0":
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await bot_menu_service.send_main_menu(whatsapp_number)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please select necessary option *(from 1 to 4)*."
                    )

        case UserStates.ASK_WHY_DISLIKE:
            match user_message:
                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "Thanks for your comments!"
                    )
                    get_recipe_id = await user_session.get_get_recipe_id()
                    rating_dto = CreateRecipeRatingDTO(
                        user_id=user.id,
                        recipe_id=get_recipe_id,
                        rating=1,
                        comment=user_message[:350] # For long message
                    )
                    await RecipeRatingsService.create_recipe_rating(uow, rating_dto)
                    
                    # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await bot_menu_service.send_main_menu(whatsapp_number)

        case UserStates.MENU_SAVE_RECIPE:
            match user_message:
                case "1":
                    # recipe_name = user_cache[whatsapp_number]["get_recipe_name"]
                    recipe_name = await user_session.get_get_recipe_name()
                    recipe_id = await user_session.get_get_recipe_id()
                    grouped_foods = await FoodService.get_grouped_foods_by_recipe_id(uow, recipe_id) #user_cache[whatsapp_number]["get_recipe_id"])
                    await bot_menu_service.send_shopping_list_recipe_after_like(whatsapp_number, grouped_foods, recipe_name)
                    # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await asyncio.sleep(1.5)
                    await bot_menu_service.send_main_menu(whatsapp_number)
                case "0":
                    # await user_states.set(whatsapp_number, UserStates.MAIN_MENU)
                    await user_session.set_state(UserStates.MAIN_MENU)
                    await bot_menu_service.send_main_menu(whatsapp_number)

                case _:
                    await bot_menu_service.send_message(
                        whatsapp_number, "❌ Invalid option. Please select necessary option *(from 1 to 0)*."
                    )

    return ""
