# Third-party model and data notices

The saved semantic encoder is `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Its upstream model card declares Apache-2.0. The accompanying `MODEL-LICENSE-Apache-2.0.txt` contains that license. The exported encoder weights are not fine-tuned; document vectors and sampled chunk pooling are computed by UpShift. The upstream model card is retained alongside the encoder.

TweetEval sentiment derives from SemEval-2017 sentiment data. It is an external research benchmark; the exact repository revision is in metadata. The raw tweets are not bundled in the backend handoff. Follow upstream dataset terms if redistributing benchmark data.

Resume.csv, postings.csv and skills_en.csv were supplied by the project. Their original dataset attribution and terms must be retained. Job descriptions in the research catalogue originate from the supplied postings dataset; this bundle is intended for the group's academic research and integration. It does not assert a new license for those descriptions or for the original CSVs.

VADER is used through NLTK. The VADER sentiment lexicon and fitted logistic-regression classifier are serialized for offline inference. Installed Python libraries keep their respective upstream licenses; see their distributions. This notice is not a replacement for upstream terms.
