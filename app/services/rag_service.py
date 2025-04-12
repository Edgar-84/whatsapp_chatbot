import re
import csv
import httpx
from supabase import AsyncClient
from app.config.logger_settings import get_logger
from app.api.dtos.recipe_user_preferences_dto import RecipeUserPreferencesDTO

logger = get_logger("rag_service")


class RagService:
    def __init__(self, openai_key: str):
        self._openai_key = openai_key

    async def get_embedding(self, text: str) -> list[float]:
        """Create embedding for given text using OpenAI API"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                json={
                    "input": text,
                    "model": "text-embedding-ada-002"
                },
                headers={
                    "Authorization": f"Bearer {self._openai_key}"
                }
            )

            if response.status_code != 200:
                raise Exception(f"Error fetching embedding: {response.text}")

            data = response.json()
            return data['data'][0]['embedding']


class SaveRecipesEmbeddings(RagService):
    def __init__(self, openai_key: str, supabase_client: AsyncClient):
        self._supabase_client = supabase_client
        self.table_for_recipe_embeddings = "recipe_embeddings"
        super().__init__(openai_key)

    @staticmethod
    def _load_recipes_from_csv(file_path: str) -> list[dict[str, str]]:
        recipes = []
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            reader.fieldnames = [name.lstrip("\ufeff") for name in reader.fieldnames]
            reader.fieldnames[0] = "id"

            for row in reader:
                recipe = (
                    row["id"], row["name"], row["sub_title"], row["preparation_method"], 
                    row["nut_recommend"], row["comment"], row["minutes"], row["meal_types"], 
                    row["ingredients"]
                )
                recipes.append(recipe)

        return recipes
    
    @staticmethod
    def _build_recipe_text(recipe: tuple[str, str, str, str, str, str, str, str, str]) -> tuple[str, str]:
        (recipe_id, name, sub_title, prep_method, nut_recommend, comment, minutes, meal_type, ingredients) = recipe
        text = f"Name: {name}\nSubtitle: {sub_title}\nPreparation Method: {prep_method}\n"
        text += f"Nutritional Recommendations: {nut_recommend}\nComment: {comment}\n"
        text += f"Preparation Time: {minutes} minutes\nMeal Type: {meal_type}\nIngredients: {ingredients}"
        return recipe_id, text

    def _upsert_embedding_to_supabase(self, recipe_id: str, embedding: list[float]):
        """
        Save recipe embedding to Supabase
        """

        data = {
            "recipe_id": recipe_id,
            "embedding_vector": embedding
        }
        response = self._supabase_client.table(self.table_for_recipe_embeddings).upsert(data).execute()
        return response

    def save_recipes(self, recipes_csv_path: str):
        """
        Prepare embedings from CSV file and save to Supabase
        """

        recipes = self._load_recipes_from_csv(recipes_csv_path)
        recipe_embeddings = {}

        for recipe in recipes:
            recipe_id, text = self._build_recipe_text(recipe)
            logger.debug(f"Processing recipe {recipe_id}...")
            embedding = self.get_embedding(text)
            recipe_embeddings[recipe_id] = embedding
            logger.debug(f"Embedding created for recipe {recipe_id}")
            
            # Save in Supabase
            self._upsert_embedding_to_supabase(recipe_id, embedding)


class AskRagForRecipe(RagService):
    def __init__(self, openai_key: str, supabase_client: AsyncClient, csv_file_path: str):
        self._supabase_client = supabase_client
        self._csv_file_path = csv_file_path
        self._source_table = "recipes_view_data"
        super().__init__(openai_key)
    
    async def _load_recipes_from_db(self, recipe_ids: list[int]) -> list[dict[str, str]]:
        """
        Load recipes from Supabase table 'recipes_view_data'
        """
        response = await self._supabase_client.table(self._source_table).select("*").execute()
        if not recipe_ids:
            return []

        response = await self._supabase_client.table(self._source_table).select("*").in_("id", recipe_ids).execute()    
        recipes = response.data  # This is a list of dicts
        return recipes

    async def ask_recipe(self, client_response: RecipeUserPreferencesDTO) -> str:
        client_response = client_response.model_dump()
        logger.info(f" ===> Client request for RAG: {client_response}")
        query_embedding = await self._get_query_embedding(client_response)
        # logger.info(f"Guery embedding: {query_embedding}")
        similar_recipes = await self._search_similar_embeddings(query_embedding)

        # NEW
        recipe_ids = [int(r["recipe_id"]) for r in similar_recipes]

        # recipes = self.get_recipes_from_csv_by_ids(self._csv_file_path, recipe_ids)
        recipes = await self._load_recipes_from_db(recipe_ids)

        # END new
        banned_foods = client_response.get("banned_foods", [])
        logger.info(f"Banned foods: {banned_foods}")
        logger.info(f"Recipes: {recipes[:10]}")
        filtered_recipes = self._filter_recipes(recipes, banned_foods)
        for i in filtered_recipes:
            logger.debug(f"Filtered recipe {i}")

        logger.info(f"Filtered recipes count: {len(filtered_recipes)}")
        result_after_asc_ai, recipe_id = await self._ask_openai_for_best_recipe(filtered_recipes, client_response)
        logger.debug(f"Result after ASC AI:\n{result_after_asc_ai}\n Recipe_ID: {recipe_id}")

        selected_recipe = next((r for r in filtered_recipes if r["id"] == int(recipe_id)), None)
        logger.debug(f"Selected recipe: {selected_recipe}")

        if not selected_recipe:
            logger.warning(f"Recipe ID {recipe_id} not found in filtered recipes.")
            return result_after_asc_ai, recipe_id, "Not found"  # fallback

        recipe_details = (
            f"\n\n*Selected Recipe:*\n"
            f"*Name:* {selected_recipe.get('name')}\n"
            f"*Preparation Time:* {selected_recipe.get('minutes')} minutes\n"
            f"*Foods:* {selected_recipe.get('foods')}\n"
            f"*Ingredients:* {selected_recipe.get('ingredients')}\n"
            # f"*Preparation Method:* {selected_recipe.get('preparation_method')}"
        )

        final_response = result_after_asc_ai + recipe_details
        logger.debug(f"Final response:\n{final_response}\n Recipe_ID: {recipe_id}")
        return final_response, recipe_id, selected_recipe.get('name')
    
    async def _search_similar_embeddings(self, query_embedding: list[float]) -> list[str]:
        """
        Search for similar embeddings in Supabase using cosine similarity
        """
        response_data = await self._supabase_client.rpc("match_recipes",{
                "query_embedding": query_embedding,
                "match_count": 10
            }).execute()
        logger.info(f"Resp: {response_data}")
        response_data = response_data.data

        if response_data:
            logger.debug(f"Found similar recipes [{len(response_data)}]: {response_data}")
            results = response_data
            filtered_results = [r for r in results if r["similarity"] >= 0.75]
            logger.debug(f"Filtered results [{len(filtered_results)}]: {filtered_results}")
            return filtered_results
        else:
            logger.debug("No similar recipes found.")
            return []
    
    @staticmethod
    def _filter_recipes(candidate_recipes, banned_foods_list):
        """
        Filter recipes that contain banned foods
        """

        filtered = []
        for recipe in candidate_recipes:
            # Assume recipe includes a field "ingredients" that is a string listing the ingredients.
            if any(banned.lower() in recipe["foods"].lower() for banned in banned_foods_list):
                logger.debug(f"Skipping recipe {recipe['id']} due to banned ingredient")
                continue  # skip recipes that contain any banned ingredient
            filtered.append(recipe)

        return filtered

    async def _get_query_embedding(self, client_response: dict[str, str]) -> list[float]:
        query_text = self.__build_query_text(
            meal_type=client_response.get("meal_type", "No preference"),
            dietary_pref=client_response.get("dietary_pref", "No preference"),
            include_ingredients=client_response.get("include_ingredients", ""),
            additional_notes=client_response.get("additional_notes", ""),
            # banned_foods=client_response.get("banned_foods", "")
        )
        result = await self.get_embedding(query_text)
        # logger.debug(f"Embeding for query: {result}")
        return result
    
    def get_recipes_from_csv_by_ids(self, file_path: str, recipe_ids: list[str]) -> list[dict]:
        """
        Download recipes from CSV by IDs
        """
        recipes = {}

        # Read CSV and create dictionary {id: recipe_data}
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            reader.fieldnames = [name.lstrip("\ufeff") for name in reader.fieldnames]
            reader.fieldnames[0] = "id"

            for row in reader:
                recipe_id = row["id"]
                recipes[recipe_id] = {
                    "recipe_id": recipe_id,
                    "name": row["name"],
                    "sub_title": row["sub_title"],
                    "preparation_method": row["preparation_method"],
                    "nut_recommend": row["nut_recommend"],
                    "comment": row["comment"],
                    "minutes": row["minutes"],
                    "meal_types": row["meal_types"],
                    "ingredients": row["ingredients"]
                }
                # logger.debug(f"Loaded recipe {recipe_id}: {row}")
                # logger.debug(f"Recipes dictionary: {recipes[recipe_id]}")

        # Filter only recipes that exist in the provided ID list
        filtered_recipes = [recipes[rid] for rid in recipe_ids if rid in recipes]

        return filtered_recipes

    @staticmethod
    def __build_query_text(
            meal_type: str,
            dietary_pref: str,
            include_ingredients: str,
            additional_notes: str,
            # banned_foods: str
        ) -> str:
        """
        Build query text from client response
        """

        query_parts = [
            f"Meal type: {meal_type}",
            f"Dietary preference: {dietary_pref}",
        ]
        if include_ingredients:
            query_parts.append(f"Must include at least one of them ingredients: {include_ingredients}")
        if additional_notes:
            query_parts.append(f"Additional requirements: {additional_notes}")
        # if banned_foods:
        #     query_parts.append(f"Must NOT include: {banned_foods}")
        result = "\n".join(query_parts)
        logger.debug(f"Result for client response: {result}")
        return result

    def _prepare_ai_prompt(self, recipes, client_response):
        """
        Take recipes from RAG and prepare AI prompt, in natural language, with fallback logic.
        """
        prompt = (
            "You are a professional nutritionist helping a client choose the most suitable recipe.\n"
            "Your task is to analyze the provided client preferences and a set of available recipes.\n"
            "You need to find only one best match.\n"
            "If none of the available recipes contain the specified 'must include' ingredients, "
            "you must still choose the best match based on all *other* preferences.\n"
            "In this case, mention this clearly and explain your reasoning.\n\n"

            "Structure your response as follows:\n"
            "1. A friendly explanation of your recommendation, mentioning why it fits the client's needs.\n"
            "2. At the end, in square brackets, ONLY include the internal recipe ID (e.g., [RECIPE_ID: abc123]), "
            "but do NOT mention this to the client.\n\n"
        )

        # Include client preferences
        prompt += "Client Preferences:\n"
        prompt += f"- Meal Type: {client_response.get('meal_type', 'No preference')}\n"
        prompt += f"- Dietary Preference: {client_response.get('dietary_pref', 'No preference')}\n"

        included_ingredients = client_response.get("include_ingredients", "").strip()
        if included_ingredients:
            prompt += f"- Must Include Ingredients: {included_ingredients[:350]}\n" # For case if user try to send long message

        banned_foods = client_response.get("banned_foods", [])
        if banned_foods:
            prompt += f"- Forbidden Ingredients: {', '.join(banned_foods)}\n"

        additional_notes = client_response.get("additional_notes", "").strip()
        if additional_notes:
            prompt += f"- Additional Notes: {additional_notes}\n"

        prompt += "\nAvailable Recipes:\n"
        for idx, recipe in enumerate(recipes, start=1):
            recipe_id = recipe.get("id")
            prompt += f"Recipe {recipe_id}:\n"
            prompt += f"Name: {recipe.get('name', 'Unknown')}\n"
            prompt += f"Subtitle: {recipe.get('sub_title', 'Unknown')}\n"
            prompt += f"Preparation Time: {recipe.get('minutes', 'Unknown')} minutes\n"
            prompt += f"Meal Type: {recipe.get('meal_type', 'Unknown')}\n"
            prompt += f"Foods: {recipe.get('foods', 'Unknown')}\n"
            prompt += f"Ingredients: {recipe.get('ingredients')}\n"
            prompt += f"Preparation Method: {recipe.get('preparation_method', 'Unknown')}\n"
            # We don't expose this to the user, but include ID for extraction
            prompt += f"[RECIPE_ID: {recipe_id}]\n\n"

        return prompt

    async def _ask_openai_for_best_recipe(self, recipes, client_response):
        prompt = self._prepare_ai_prompt(recipes, client_response)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful and friendly nutritionist."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.85
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Error calling OpenAI API: {response.text}")

        data = response.json()
        # Count tokens
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Example price (update when needed)
        # GPT-4 Turbo (April 2024): $0.01 per 1K prompt tokens, $0.03 per 1K completion
        cost_prompt = (prompt_tokens / 1000) * 0.01
        cost_completion = (completion_tokens / 1000) * 0.03
        total_cost = cost_prompt + cost_completion
        logger.info(f"OpenAI Token Usage — Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        logger.info(f"Estimated Cost: ${total_cost:.4f}")

        message = data["choices"][0]["message"]["content"]
        logger.info(f"Response from OpenAI: {message}")

        # Extract recipe ID from format like [RECIPE_ID: abc123]
        match = re.search(r"\[RECIPE_ID:\s*(\w+)\]", message)
        recipe_id = match.group(1) if match else None

        # Clean message from RECIPE_ID
        cleaned_message = re.sub(r"\[RECIPE_ID:.*?\]", "", message).strip()
        ltr_fix = "\u200E"
        cleaned_message = ltr_fix + cleaned_message

        return cleaned_message, recipe_id
