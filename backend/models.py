"""Load the trusted schema-2 model for the Firebase-protected API."""
import logging
import os
from pathlib import Path

from .errors import Problem

logger = logging.getLogger(__name__)


class Models:
    def __init__(self):
        self.bundle = None
        self.service = None
        self.state = 'not_configured'
        model_path = os.getenv('UPSHIFT_MODEL_PATH')
        if not model_path:
            return

        try:
            from upshift_ai.handoff import ModelService

            path = Path(model_path)
            service = ModelService(path.parent, bundle_path=path)
            service.prepare()
        except Exception:
            logger.exception('Could not load the UpShift model artifacts.')
            self.state = 'unavailable'
            return

        self.bundle = service.bundle
        self.service = service
        self.state = 'ready'

    def _ready(self):
        if self.service is None:
            raise Problem(503, 'model_unavailable', 'The UpShift model is not loaded.')

    def recommendations(self, text, top_k):
        self._ready()
        return self.service.recommendations(text, top_k)

    def recommendations_from_vacancies(self, text, vacancies, top_k=5):
        self._ready()
        return self.service.rank_vacancies(text, vacancies, top_k)

    def sentiment(self, text):
        self._ready()
        if self.bundle.get('sentiment') is None:
            raise Problem(503, 'sentiment_unavailable', 'No trained sentiment model is available.')
        return self.service.sentiment(text)
