"""Transactional Firestore persistence. MemoryStore is for isolated tests only."""
import copy
import os
import threading
from .errors import Problem


class FirestoreListingStore:
    def __init__(self):
        self._db = None
        self._lock = threading.Lock()

    def db(self):
        with self._lock:
            if self._db is None:
                project = os.getenv('UPSHIFT_FIREBASE_PROJECT_ID', '')
                emulator = os.getenv('FIRESTORE_EMULATOR_HOST')
                if not project or (emulator and (not project.startswith('demo-') or
                        emulator not in ('127.0.0.1:8080', 'localhost:8080'))):
                    raise Problem(503, 'listing_store_unavailable', 'Configure Firestore credentials or a local demo emulator.')
                try:
                    from google.cloud import firestore
                    self._db = firestore.Client(project=project)
                except Exception:
                    raise Problem(503, 'listing_store_unavailable', 'Firestore credentials could not be initialized.')
        return self._db

    def get(self, collection, key):
        snapshot = self.db().collection(collection).document(key).get()
        return snapshot.to_dict() if snapshot.exists else None

    def transact(self, keys, change):
        from google.cloud import firestore
        db = self.db()

        @firestore.transactional
        def run(transaction):
            refs = {key: db.collection(key[0]).document(key[1]) for key in keys}
            rows = {}
            for key, ref in refs.items():
                snap = ref.get(transaction=transaction)
                rows[key] = snap.to_dict() if snap.exists else None
            updates, result = change(rows)
            for key, value in updates.items():
                transaction.set(db.collection(key[0]).document(key[1]), value)
            return result
        return run(db.transaction())

    def list(self, collection, *, owner=None, after='', limit=50):
        from google.cloud.firestore_v1.base_query import FieldFilter
        ref = self.db().collection(collection)
        query = ref.order_by('__name__')
        if owner is not None:
            query = query.where(filter=FieldFilter('owner_uid', '==', owner))
        if after:
            query = query.start_after({'__name__': ref.document(after)})
        docs = list(query.limit(limit + 1).stream())
        return {'items': [d.to_dict() for d in docs[:limit]],
                'next_cursor': docs[limit-1].id if len(docs) > limit else None}


class MemoryStore:
    """Explicitly injected by tests; never selected through an HTTP request."""
    def __init__(self):
        self.rows = {}
        self.lock = threading.RLock()

    def get(self, collection, key):
        with self.lock:
            return copy.deepcopy(self.rows.get((collection, key)))

    def transact(self, keys, change):
        with self.lock:
            rows = {key: copy.deepcopy(self.rows.get(key)) for key in keys}
            updates, result = change(rows)
            self.rows.update(copy.deepcopy(updates))
            return copy.deepcopy(result)

    def list(self, collection, *, owner=None, after='', limit=50):
        with self.lock:
            items = [copy.deepcopy(v) for (c, key), v in sorted(self.rows.items())
                     if c == collection and key > after and (owner is None or v.get('owner_uid') == owner)]
            return {'items': items[:limit], 'next_cursor': items[limit-1]['id'] if len(items) > limit else None}
