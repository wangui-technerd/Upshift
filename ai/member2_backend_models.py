"""Copy to backend/models.py; put delivered upshift_ai/ on PYTHONPATH.

Replaces the old schema-1-only adapter; Firebase routes/auth remain Member 2's.
"""
import os
from pathlib import Path
from .errors import Problem


class Models:
    def __init__(self):
        self.bundle=None
        self.service=None
        self.state='not_configured'
        self.load_error=None
        path=os.getenv('UPSHIFT_MODEL_PATH')
        if not path:return
        try:
            from upshift_ai.handoff import ModelService
            self.service=ModelService(Path(path).parent)
            self.bundle=self.service.bundle
            self.state='ready'
        except Exception as error:
            self.load_error=str(error)
            self.state='unavailable'

    def _ready(self):
        if self.service is None:raise Problem(503,'model_unavailable','The delivered schema-2 model is not loaded.')

    def recommendations(self,text,top_k):
        self._ready()
        return self.service.recommendations(text,top_k)

    def recommendations_from_vacancies(self,text,vacancies,top_k=5):
        self._ready()
        return self.service.rank_vacancies(text,vacancies,top_k)

    def sentiment(self,text):
        self._ready()
        return self.service.sentiment(text)
