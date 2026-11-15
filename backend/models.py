"""Optional adapter for the trusted artifact produced by the UpShift notebook."""
import os
from pathlib import Path

from .errors import Problem


class Models:
    def __init__(self):
        self.bundle = None
        self.state = 'not_configured'
        path = os.getenv('UPSHIFT_MODEL_PATH')
        if not path:
            return
        try:
            # joblib executes pickle code: only load your own trusted notebook output.
            import joblib
            self.bundle = joblib.load(Path(path))
            required = {'schema_version', 'retriever', 'job_vectors', 'jobs', 'skill_lookup', 'job_skills'}
            if not required <= self.bundle.keys() or self.bundle['schema_version'] != 1:
                raise ValueError('Unsupported notebook artifact')
            self.state = 'ready'
        except Exception:
            self.bundle = None
            self.state = 'unavailable'

    def recommendations(self, text, top_k):
        if self.bundle is None:
            raise Problem(503, 'model_unavailable', 'The notebook model artifact is not loaded.')
        from .upshift_inference import recommend
        result = recommend(self.bundle, text, top_k)
        return {**result, 'method': 'tfidf_cosine', 'model_version': 'notebook-schema-1',
                'score_definition': 'TF-IDF cosine text similarity, not skill coverage or a hiring probability.',
                'catalogue': 'notebook_research_jobs',
                'limitations': ['Research listings may be expired or outside Kenya.',
                                'Skills not mentioned are not proof of missing ability.']}

    def sentiment(self, text):
        model = self.bundle.get('sentiment_model') if self.bundle else None
        if model is None:
            raise Problem(503, 'sentiment_unavailable', 'No trained sentiment model is present in the notebook artifact.')
        return {'label': str(model.predict([text])[0]), 'method': 'notebook_sentiment_classifier',
                'model_version': 'notebook-schema-1'}
