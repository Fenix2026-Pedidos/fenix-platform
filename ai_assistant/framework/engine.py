import logging

from google import genai
from google.genai import types

from .governance import SynergIAGovernance

logger = logging.getLogger(__name__)


class SynergIAEngine:
    """Motor Gemini basado en el SDK oficial Google Gen AI."""

    def __init__(self, api_key):
        self.primary_model_name = 'gemini-2.5-pro'
        self.fallback_model_name = 'gemini-2.5-flash'
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.safety_settings = [
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_MEDIUM_AND_ABOVE'),
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_MEDIUM_AND_ABOVE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_MEDIUM_AND_ABOVE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_MEDIUM_AND_ABOVE'),
        ]

    @staticmethod
    def _history_contents(history):
        contents = []
        for item in history or []:
            role = 'model' if item.get('role') in {'assistant', 'model'} else 'user'
            value = item.get('parts', item.get('content', ''))
            if isinstance(value, list):
                value = ' '.join(str(part.get('text', part) if isinstance(part, dict) else part) for part in value)
            if value:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=str(value)[:4000])]))
        return contents[-20:]

    def _get_response(self, model_name, message, history, system_instruction):
        if not self.client:
            raise RuntimeError('GOOGLE_API_KEY no configurada')
        contents = self._history_contents(history)
        contents.append(types.Content(role='user', parts=[types.Part.from_text(text=message)]))
        response = self.client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                safety_settings=self.safety_settings,
            ),
        )
        return response.text

    def ask(self, message, history=None, knowledge_base='', is_authenticated=False):
        system_instruction = SynergIAGovernance.get_system_prompt(
            knowledge_base, is_authenticated=is_authenticated
        )
        try:
            return self._get_response(self.primary_model_name, message, history, system_instruction)
        except Exception:
            logger.exception('Error en modelo primario; se usa el fallback')
            return self._get_response(self.fallback_model_name, message, history, system_instruction)
