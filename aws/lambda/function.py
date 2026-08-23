# Import Alexa Skills Kit SDK
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# Import custom modules
from src.llm import N_A_M_I

# Instantiate once per warm Lambda container, not per invocation
# This avoids rebuilding the Bedrock client/re-reading the persona file every call
nami = N_A_M_I()


class LaunchRequestHandler(AbstractRequestHandler):
    """
    Handles "Alexa, open Varun".
    """

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak("Welcome to Varun. Tell me an expense to log.")
            .set_should_end_session(False)
            .response
        )


class LogExpenseIntentHandler(AbstractRequestHandler):
    """
    Handles "Alexa, tell Varun to log 40 dollars for dinner split with Bob".
    """

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("LogExpenseIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots or {}
        query = slots["query"].value if "query" in slots else None

        if not query:
            return (
                handler_input.response_builder
                .speak("I didn't catch that. Try again?")
                .set_should_end_session(False)
                .response
            )

        verdict = nami.run(query)

        return (
            handler_input.response_builder
            .speak(verdict.text)
            .set_should_end_session(True)
            .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Fallback so a Splitwise failure doesn't just hang Alexa.
    """

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        return (
            handler_input.response_builder
            .speak("Something went wrong while using the Splitwise API. Try again shortly.")
            .set_should_end_session(True)
            .response
        )


# Instantiate the Alexa SkillBuilder
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(LogExpenseIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()
