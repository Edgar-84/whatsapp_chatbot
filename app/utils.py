import asyncio
from twilio.rest import Client
from app.config.logger_settings import get_logger


logger = get_logger(__name__)


class MessageClient:
    """
    Work with messages through Twilio
    """

    def __init__(self, account_sid, auth_token, twilio_number):
        self.client = Client(account_sid, auth_token)
        self.twilio_number = twilio_number

    async def send_message(self, to_number: str, body_text: str):
        try:
            message = await asyncio.to_thread(
                self.client.messages.create,
                from_=f"whatsapp:{self.twilio_number}",
                body=body_text,
                to=f"whatsapp:{to_number}"
            )
            logger.info(f"Message sent to {to_number}: {message.body}")
        except Exception as e:
            logger.error(f"Error sending message to {to_number}: {e}")

    async def send_interactive_message(self, to_number: str, body: str, buttons: list):
        try:
            message = await asyncio.to_thread(
                self.client.messages.create,
                from_=f"whatsapp:{self.twilio_number}",
                to=f"whatsapp:{to_number}",
                interactive={
                    "type": "button",
                    "body": {"text": body},
                    "action": {"buttons": buttons}
                }
            )
            logger.info(f"Interactive message: {message} sent to {to_number}")
        except Exception as e:
            logger.error(f"Error sending interactive message to {to_number}: {e}")


# # Sending message logic through Twilio Messaging API
# def send_message(to_number, body_text):
#     try:
#         message = client.messages.create(
#             from_=f"whatsapp:{twilio_number}",
#             body=body_text,
#             to=f"whatsapp:{to_number}"
#             )
#         logger.info(f"Message sent to {to_number}: {message.body}")
#     except Exception as e:
#         logger.error(f"Error sending message to {to_number}: {e}")


# def send_interactive_message(to_number, header, body, buttons):
#     try:
#         message = client.messages.create(
#             from_=f"whatsapp:{twilio_number}",
#             to=f"whatsapp:{to_number}",
#             content_type="application/json",
#             interactive={
#                 "type": "button",
#                 "body": {"text": body},
#                 "action": {"buttons": buttons}
#             }
#         )
#         logger.info(f"Interactive message sent to {to_number}")
#     except Exception as e:
#         logger.error(f"Error sending interactive message to {to_number}: {e}")