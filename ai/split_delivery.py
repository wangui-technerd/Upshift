"""Create two independently extractable Drive archives below its transport limit."""
from pathlib import Path
import json,zipfile,shutil,hashlib
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'output/ai'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb')as source:
        for block in iter(lambda:source.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def split():
    targets=[OUT/'upshift_ai_core.zip',OUT/'upshift_semantic_encoder.zip']
    with zipfile.ZipFile(OUT/'upshift_ai_handoff.zip')as source:
        archives=[zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED)for p in targets]
        try:
            for name in source.namelist():
                target=archives[int(name.startswith('semantic_encoder/'))]
                with source.open(name)as incoming,target.open(name,'w')as outgoing:
                    shutil.copyfileobj(incoming,outgoing,1024*1024)
        finally:
            for archive in archives:archive.close()
        union=set()
        expected=json.loads(source.read('SHA256SUMS.json'))
        for path in targets:
            assert path.stat().st_size<100*1024*1024
            with zipfile.ZipFile(path)as archive:
                assert archive.testzip()is None
                for name in archive.namelist():
                    assert name not in union
                    union.add(name)
                    if name in expected:
                        h=hashlib.sha256()
                        with archive.open(name)as member:
                            for chunk in iter(lambda:member.read(1024*1024),b''):h.update(chunk)
                        assert h.hexdigest()==expected[name],name
        assert union==set(source.namelist())
    manifest=json.loads((OUT/'delivery_manifest.json').read_text())
    manifest['drive_archives']={p.name:{'bytes':p.stat().st_size,'sha256':digest(p)}for p in targets}
    manifest['verification']='Archive union equals full handoff; every file checksum verified.'
    (OUT/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
    (OUT/'DOWNLOAD_AND_SETUP.md').write_text('''# Download and set up UpShift AI

Download **both** `upshift_ai_core.zip` and `upshift_semantic_encoder.zip`. They are separate archives because the upload tool has a 100 MB per-file limit.

1. Create one empty folder, for example `upshift-ai`.
2. Extract both ZIPs into that same folder. Avoid an extra nested folder for either archive.
3. Check that `api.py`, `upshift_bundle.joblib`, and the `semantic_encoder` folder sit beside one another.
4. Read `MODEL_HANDOFF.md` for measured results and `PROJECT_GUIDE.md` for setup and API instructions. Install CPU PyTorch from its official CPU index first if you want CPU-only dependencies, then install requirements.

The model bundle and encoder run locally after installation; no paid inference API is required. Raw training CSVs are not included. The executed notebook is also available separately in this Drive folder; a fresh Colab run uses the project's existing raw datasets.

`delivery_manifest.json` contains archive checksums, and `SHA256SUMS.json` inside the core archive contains individual file checksums. The split archives were verified to reproduce every member of the complete local handoff.
''',encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)
if __name__=='__main__':split()
