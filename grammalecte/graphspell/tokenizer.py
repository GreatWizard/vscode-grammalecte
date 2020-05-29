"""
Very simple tokenizer
using regular expressions
"""

import re

from unicodedata import normalize

_PATTERNS = {
    "default":
        (
            r'(?P<FOLDERUNIX>/(?:bin|boot|dev|etc|home|lib|mnt|opt|root|sbin|tmp|usr|var|Bureau|Documents|Images|Musique|Public|Téléchargements|Vidéos)(?:/[\w.()-]+)*)',
            r'(?P<FOLDERWIN>[a-zA-Z]:\\(?:Program Files(?: [(]x86[)]|)|[\w.()]+)(?:\\[\w.()-]+)*)',
            r'(?P<PUNC>[][,.;:!?…«»“”‘’"(){}·–—¿¡])',
            r'(?P<WORD_ACRONYM>[A-Z][.][A-Z][.](?:[A-Z][.])*)',
            r'(?P<LINK>(?:https?://|www[.]|\w+[@.]\w\w+[@.])\w[\w./?&!%=+*"\'@$#-]+)',
            r'(?P<HASHTAG>[#@][\w-]+)',
            r'(?P<HTML><\w+.*?>|</\w+ *>)',
            r'(?P<PSEUDOHTML>\[/?\w+\])',
            r'(?P<HOUR>\d\d?[h:]\d\d(?:[m:]\d\ds?|)\b)',
            r'(?P<NUM>\d+(?:[.,]\d+))',
            r'(?P<SIGN>[&%‰€$+±=*/<>⩾⩽#|×¥£§¢¬÷@-])',
            r"(?P<WORD>\w+(?:[’'`-]\w+)*)"
        ),
    "fr":
        (
            r'(?P<FOLDERUNIX>/(?:bin|boot|dev|etc|home|lib|mnt|opt|root|sbin|tmp|usr|var|Bureau|Documents|Images|Musique|Public|Téléchargements|Vidéos)(?:/[\w.()-]+)*)',
            r'(?P<FOLDERWIN>[a-zA-Z]:\\(?:Program Files(?: [(]x86[)]|)|[\w.()]+)(?:\\[\w.()-]+)*)',
            r'(?P<PUNC>[][,.;:!?…«»“”‘’"(){}·–—¿¡])',
            r'(?P<WORD_ACRONYM>[A-Z][.][A-Z][.](?:[A-Z][.])*)',
            r'(?P<LINK>(?:https?://|www[.]|\w+[@.]\w\w+[@.])\w[\w./?&!%=+*"\'@$#-]+)',
            r'(?P<HASHTAG>[#@][\w-]+)',
            r'(?P<HTML><\w+.*?>|</\w+ *>)',
            r'(?P<PSEUDOHTML>\[/?\w+\])',
            r"(?P<WORD_ELIDED>(?:l|d|n|m|t|s|j|c|ç|lorsqu|puisqu|jusqu|quoiqu|qu|presqu|quelqu)['’´‘′`ʼ])",
            r'(?P<WORD_ORDINAL>\d+(?:ers?|res?|è[rm]es?|i[èe][mr]es?|de?s?|nde?s?|ès?|es?|ᵉʳˢ?|ʳᵉˢ?|ᵈᵉ?ˢ?|ⁿᵈᵉ?ˢ?|ᵉˢ?)\b)',
            r'(?P<HOUR>\d\d?[h:]\d\d(?:[m:]\d\ds?|)\b)',
            r'(?P<NUM>\d+(?:[.,]\d+|))',
            r'(?P<SIGN>[&%‰€$+±=*/<>⩾⩽#|×¥£¢§¬÷@-])',
            r"(?P<WORD>[\w\u0300-\u036f]+(?:[’'`-][\w\u0300-\u036f]+)*)"
        )
}


class Tokenizer:
    "Tokenizer: transforms a text in a list of tokens"

    def __init__ (self, sLang):
        self.sLang = sLang
        if sLang not in _PATTERNS:
            self.sLang = "default"
        self.zToken = re.compile( "(?i)" + '|'.join(sRegex for sRegex in _PATTERNS[sLang]) )

    def genTokens (self, sText, bStartEndToken=False):
        "generator: tokenize <sText>"
        i = 0
        if bStartEndToken:
            yield { "i": 0, "sType": "INFO", "sValue": "<start>", "nStart": 0, "nEnd": 0, "lMorph": ["<start>"] }
        for i, m in enumerate(self.zToken.finditer(sText), 1):
            yield { "i": i, "sType": m.lastgroup, "sValue": normalize("NFC", m.group()), "nStart": m.start(), "nEnd": m.end() }
        if bStartEndToken:
            iEnd = len(sText)
            yield { "i": i+1, "sType": "INFO", "sValue": "<end>", "nStart": iEnd, "nEnd": iEnd, "lMorph": ["<end>"] }

    def getTokenTypes (self):
        "returns list of token types as tuple (token name, regex)"
        return [ sRegex[4:-1].split(">")  for sRegex in _PATTERNS[self.sLang] ]
