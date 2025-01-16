import logging
import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from openai import OpenAI
from config import API_KEY

client = OpenAI(api_key=API_KEY)


# Configuração da API OpenAI

# Configuração de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Mensagens de contexto para o ChatGPT
messages = [
    {
        "role": "system",
        "content": "Você é uma assistente muito útil. Por favor, responda de forma clara e concisa em Português do Brasil.",
    }
]


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler para iniciar a skill."""

    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "Bem vindo ao Chat 'Gepetê Quatro' da 'Open ei ai'! Qual a sua pergunta?"
        )

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler para lidar com o Intent de consulta ao ChatGPT."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # Obtém a consulta do slot "query"
        query = ask_utils.get_slot_value(handler_input, "query")
        if not query:
            return (
                handler_input.response_builder.speak(
                    "Desculpe, não entendi sua pergunta. Por favor, tente novamente."
                )
                .ask("Qual a sua pergunta?")
                .response
            )

        try:
            # Gera a resposta usando o ChatGPT
            response = generate_gpt_response(query)
            return (
                handler_input.response_builder.speak(response)
                .ask("Você tem mais alguma dúvida?")
                .response
            )
        except Exception as e:
            logger.error(f"Erro ao gerar resposta do ChatGPT: {e}")
            return (
                handler_input.response_builder.speak(
                    "Desculpe, houve um problema ao processar sua solicitação. Por favor, tente novamente."
                )
                .ask("Gostaria de tentar novamente?")
                .response
            )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Handler para lidar com Intents de Cancelamento ou Parada."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(
            handler_input
        ) or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Saindo do modo Chat Gepetê. Até logo!"
        return handler_input.response_builder.speak(speak_output).response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Handler genérico para capturar erros."""

    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speak_output = (
            "Desculpe, ocorreu um erro. Por favor, tente novamente mais tarde."
        )

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


def generate_gpt_response(query):
    """Gera a resposta usando o ChatGPT."""
    try:
        messages.append({"role": "user", "content": query})
        response = client.chat.completions.create(
            model="gpt-4", messages=messages, max_tokens=1000, temperature=0.7
        )
        # Extração da resposta
        reply = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logger.error(f"Erro ao se comunicar com o ChatGPT: {e}")
        return "Houve um erro ao processar sua solicitação. Tente novamente mais tarde."


# Configuração do SkillBuilder
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
