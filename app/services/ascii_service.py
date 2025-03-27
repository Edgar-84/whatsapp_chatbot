import io
import csv
import asyncio
import aiohttp

from app.config.logger_settings import get_logger


logger = get_logger(__name__)


class ASCIIService:
    @staticmethod
    async def __download_csv_from_drive(file_id: str):
        """
        Download data from remote Google Drive CSV file
        """

        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    csv_content = await response.text()
                    return io.StringIO(csv_content)
                else:
                    raise Exception(f"Mistake of loading: {response.status}")

    @classmethod
    async def process_csv(cls, file_id: str) -> dict:
        """
        Process CSV data from remote Google Drive file
        """

        logger.info(f"Processing CSV file from Google Drive: {file_id}")
        csv_file = await cls.__download_csv_from_drive(file_id)
        restrictions_dict = {
            "all_restrictions": [],
            "high_sensitivity": [],
            "low_sensitivity": [],
        }
        reader = csv.reader(csv_file, delimiter=';')

        for row in reader:
            if len(row) == 8:
                try:
                    corrected_concentration = row[3].replace(',', '.') if row[3] else None
                    score = row[4].replace(',', '.') if row[4] and row[4] != '0' else row[4]

                    data_dict = {
                        "lab_code": row[0],
                        "rbio_code": row[1],
                        "type": row[2],
                        "corrected_concentration": float(corrected_concentration) if corrected_concentration else None,
                        "score": float(score) if score != '0' else int(score),
                        "customer_name": row[5],
                        "birthday": row[6]
                    }

                    if data_dict["rbio_code"].endswith("G") and score:
                        if str(score)[0] == "1":
                            product = data_dict.get("rbio_code")
                            restrictions_dict["all_restrictions"].append(data_dict)
                            restrictions_dict["low_sensitivity"].append(product.replace("G", "").replace("GK", ""))

                        elif str(score)[0] == "2":
                            product = data_dict.get("rbio_code")
                            restrictions_dict["all_restrictions"].append(data_dict)
                            restrictions_dict["high_sensitivity"].append(product.replace("G", "").replace("GK", ""))

                except Exception as ex:
                    logger.warning(f"❌ Error processing row: {ex}")

        return restrictions_dict
