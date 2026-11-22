"""Chunked local embeddings; no document text is sent to hosted inference."""

import hashlib, json
from pathlib import Path
import numpy as np

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def text_chunks(text, words=160, stride=120, max_chunks=4):
    tokens = str(text).split()
    if not tokens:
        return [""]
    starts = list(range(0, len(tokens), stride))
    if len(starts) > max_chunks:
        starts = [
            starts[i] for i in np.linspace(0, len(starts) - 1, max_chunks, dtype=int)
        ]
    return [" ".join(tokens[i : i + words]) for i in starts]


def load_encoder(path=None):
    import torch
    from sentence_transformers import SentenceTransformer

    torch.set_num_threads(2)
    if path is not None:
        path = Path(path).resolve(strict=True)
        model = SentenceTransformer(str(path), device="cpu", local_files_only=True)
    else:
        model = SentenceTransformer(MODEL_ID, revision=MODEL_REVISION, device="cpu")
    model.max_seq_length = 256
    return model


def encode_documents(model, texts, cache_path=None):
    digest = hashlib.sha256(
        json.dumps(list(texts), ensure_ascii=False).encode()
    ).hexdigest()
    settings = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "max_chunks": 4,
        "words_per_chunk": 160,
        "stride": 120,
        "max_seq_length": 256,
    }
    if cache_path:
        cache_path = Path(cache_path)
        meta = cache_path.with_suffix(".json")
        if cache_path.exists() and meta.exists():
            saved = json.loads(meta.read_text())
            if saved.get("sha256") == digest and all(
                saved.get(k) == v for k, v in settings.items()
            ):
                return np.load(cache_path)
    groups = [text_chunks(t) for t in texts]
    flat = [c for group in groups for c in group]
    print(f"Embedding {len(texts)} documents in {len(flat)} sampled chunks", flush=True)
    embeddings = model.encode(
        flat,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    rows = []
    pos = 0
    for group in groups:
        vector = embeddings[pos : pos + len(group)].mean(axis=0)
        pos += len(group)
        rows.append(vector / max(np.linalg.norm(vector), 1e-12))
    vectors = np.asarray(rows, dtype=np.float32)
    if cache_path:
        np.save(cache_path, vectors)
        meta.write_text(json.dumps({"sha256": digest, **settings}))
    return vectors
