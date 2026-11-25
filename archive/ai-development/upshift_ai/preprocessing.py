"""Shared preprocessing for training and serving."""
import html
import re
import unicodedata

TOKEN_PATTERN=r"(?u)(?:\.net\b|\b\w+(?:[.+#-]\w+)*(?:\+\+|#)?)"
SECTION_WORDS={'summary','skills','experience','education','objective','profile','highlights','qualifications','career','professional'}
def plain_text(value):
    if not isinstance(value,str):return ''
    value=html.unescape(unicodedata.normalize('NFKC',value))
    value=re.sub(r'<[^>]+>',' ',value)
    return value.replace('\r\n','\n').replace('\r','\n').strip()

def clean_text(value):
    value=plain_text(value).lower()
    value=re.sub(r'https?://\S+|www\.\S+|\S+@\S+',' ',value)
    return re.sub(r'\s+',' ',re.sub(r'[^\w+#.\s-]',' ',value)).strip()

def prepare_resume(value):
    value=plain_text(value)
    for _ in range(2):
        pieces=re.split(r'\s{2,}|\n',value,maxsplit=1)
        chunk=pieces[0];letters=[c for c in chunk if c.isalpha()]
        first=(re.findall(r'[a-z]+',chunk.lower())or[''])[0]
        if len(pieces)==2 and 0<len(chunk)<=80 and letters and sum(c.isupper() for c in letters)/len(letters)>.8 and first not in SECTION_WORDS:value=pieces[1].lstrip()
        else:break
    value=re.sub(r'\bcompany name\b|\bcity\s*,?\s*state\b',' ',value,flags=re.I)
    return clean_text(value)

def segments(value):
    value=plain_text(value)
    return [part.strip(' -\t') for part in re.split(r'\n+|[;•]|(?<=[.!?])\s+(?=[A-Z0-9])|\bbut\b|\bhowever\b',value,flags=re.I) if part.strip()]
