"""
List of similar chars
useful for suggestion mechanism
"""

import re
import unicodedata


_xTransCharsForSpelling = str.maketrans({
    'ſ': 's',  'ﬃ': 'ffi',  'ﬄ': 'ffl',  'ﬀ': 'ff',  'ﬅ': 'ft',  'ﬁ': 'fi',  'ﬂ': 'fl',  'ﬆ': 'st'
})

def spellingNormalization (sWord):
    "nomalization NFC and removing ligatures"
    return unicodedata.normalize("NFC", sWord.translate(_xTransCharsForSpelling))


_xTransCharsForSimplification = str.maketrans({
    'à': 'a',  'é': 'é',  'î': 'i',  'ô': 'o',  'û': 'u',  'ÿ': 'i',  "y": "i",
    'â': 'a',  'è': 'é',  'ï': 'i',  'ö': 'o',  'ù': 'u',  'ŷ': 'i',
    'ä': 'a',  'ê': 'é',  'í': 'i',  'ó': 'o',  'ü': 'u',  'ý': 'i',
    'á': 'a',  'ë': 'é',  'ì': 'i',  'ò': 'o',  'ú': 'u',  'ỳ': 'i',
    'ā': 'a',  'ē': 'é',  'ī': 'i',  'ō': 'o',  'ū': 'u',  'ȳ': 'i',
    'ç': 'c',  'ñ': 'n',  'k': 'q',  'w': 'v',
    'œ': 'oe',  'æ': 'ae',
    'ſ': 's',  'ﬃ': 'ffi',  'ﬄ': 'ffl',  'ﬀ': 'ff',  'ﬅ': 'ft',  'ﬁ': 'fi',  'ﬂ': 'fl',  'ﬆ': 'st',
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"
})

def simplifyWord (sWord):
    "word simplication before calculating distance between words"
    sWord = sWord.lower().translate(_xTransCharsForSimplification)
    sNewWord = ""
    for i, c in enumerate(sWord, 1):
        if c == 'e' or c != sWord[i:i+1]:  # exception for <e> to avoid confusion between crée / créai
            sNewWord += c
    return sNewWord.replace("eau", "o").replace("au", "o").replace("ai", "ẽ").replace("ei", "ẽ").replace("ph", "f")


_xTransNumbersToExponent = str.maketrans({
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
})

def numbersToExponent (sWord):
    "convert numeral chars to exponant chars"
    return sWord.translate(_xTransNumbersToExponent)


aVowel = set("aáàâäāeéèêëēiíìîïīoóòôöōuúùûüūyýỳŷÿȳœæAÁÀÂÄĀEÉÈÊËĒIÍÌÎÏĪOÓÒÔÖŌUÚÙÛÜŪYÝỲŶŸȲŒÆ")
aConsonant = set("bcçdfghjklmnñpqrstvwxzBCÇDFGHJKLMNÑPQRSTVWXZ")
aDouble = set("bcdfjklmnprstzBCDFJKLMNPRSTZ")  # letters that may be used twice successively


# Similar chars

d1to1 = {
    "1": "1₁liîLIÎ",
    "2": "2₂zZ",
    "3": "3₃eéèêEÉÈÊ",
    "4": "4₄aàâAÀÂ",
    "5": "5₅sgSG",
    "6": "6₆bdgBDG",
    "7": "7₇ltLT",
    "8": "8₈bB",
    "9": "9₉gbdGBD",
    "0": "0₀oôOÔ",

    "a": "aAàÀâÂáÁäÄāĀæÆ",
    "A": "AaÀàÂâÁáÄäĀāÆæ",
    "à": "aAàÀâÂáÁäÄāĀæÆ",
    "À": "AaÀàÂâÁáÄäĀāÆæ",
    "â": "aAàÀâÂáÁäÄāĀæÆ",
    "Â": "AaÀàÂâÁáÄäĀāÆæ",
    "á": "aAàÀâÂáÁäÄāĀæÆ",
    "Á": "AaÀàÂâÁáÄäĀāÆæ",
    "ä": "aAàÀâÂáÁäÄāĀæÆ",
    "Ä": "AaÀàÂâÁáÄäĀāÆæ",

    "æ": "æÆéÉaA",
    "Æ": "ÆæÉéAa",

    "b": "bB",
    "B": "Bb",

    "c": "cCçÇsSkKqQśŚŝŜ",
    "C": "CcÇçSsKkQqŚśŜŝ",
    "ç": "cCçÇsSkKqQśŚŝŜ",
    "Ç": "CcÇçSsKkQqŚśŜŝ",

    "d": "dDðÐ",
    "D": "DdÐð",

    "e": "eEéÉèÈêÊëËēĒœŒ",
    "E": "EeÉéÈèÊêËëĒēŒœ",
    "é": "eEéÉèÈêÊëËēĒœŒ",
    "É": "EeÉéÈèÊêËëĒēŒœ",
    "ê": "eEéÉèÈêÊëËēĒœŒ",
    "Ê": "EeÉéÈèÊêËëĒēŒœ",
    "è": "eEéÉèÈêÊëËēĒœŒ",
    "È": "EeÉéÈèÊêËëĒēŒœ",
    "ë": "eEéÉèÈêÊëËēĒœŒ",
    "Ë": "EeÉéÈèÊêËëĒēŒœ",

    "f": "fF",
    "F": "Ff",

    "g": "gGjJĵĴ",
    "G": "GgJjĴĵ",

    "h": "hH",
    "H": "Hh",

    "i": "iIîÎïÏyYíÍìÌīĪÿŸ",
    "I": "IiÎîÏïYyÍíÌìĪīŸÿ",
    "î": "iIîÎïÏyYíÍìÌīĪÿŸ",
    "Î": "IiÎîÏïYyÍíÌìĪīŸÿ",
    "ï": "iIîÎïÏyYíÍìÌīĪÿŸ",
    "Ï": "IiÎîÏïYyÍíÌìĪīŸÿ",
    "í": "iIîÎïÏyYíÍìÌīĪÿŸ",
    "Í": "IiÎîÏïYyÍíÌìĪīŸÿ",
    "ì": "iIîÎïÏyYíÍìÌīĪÿŸ",
    "Ì": "IiÎîÏïYyÍíÌìĪīŸÿ",

    "j": "jJgGĵĴ",
    "J": "JjGgĴĵ",

    "k": "kKcCqQ",
    "K": "KkCcQq",

    "l": "lLłŁ",
    "L": "LlŁł",

    "m": "mMḿḾ",
    "M": "MmḾḿ",

    "n": "nNñÑńŃǹǸ",
    "N": "NnÑñŃńǸǹ",

    "o": "oOôÔóÓòÒöÖōŌœŒ",
    "O": "OoÔôÓóÒòÖöŌōŒœ",
    "ô": "oOôÔóÓòÒöÖōŌœŒ",
    "Ô": "OoÔôÓóÒòÖöŌōŒœ",
    "ó": "oOôÔóÓòÒöÖōŌœŒ",
    "Ó": "OoÔôÓóÒòÖöŌōŒœ",
    "ò": "oOôÔóÓòÒöÖōŌœŒ",
    "Ò": "OoÔôÓóÒòÖöŌōŒœ",
    "ö": "oOôÔóÓòÒöÖōŌœŒ",
    "Ö": "OoÔôÓóÒòÖöŌōŒœ",

    "œ": "œŒoOôÔeEéÉèÈêÊëË",
    "Œ": "ŒœOoÔôEeÉéÈèÊêËë",

    "p": "pPṕṔ",
    "P": "PpṔṕ",

    "q": "qQcCkK",
    "Q": "QqCcKk",

    "r": "rRŕŔ",
    "R": "RrŔŕ",

    "s": "sScCçÇśŚŝŜ",
    "S": "SsCcÇçŚśŜŝ",
    "ś": "sScCçÇśŚŝŜ",
    "Ś": "SsCcÇçŚśŜŝ",
    "ŝ": "sScCçÇśŚŝŜ",
    "Ŝ": "SsCcÇçŚśŜŝ",

    "t": "tT",
    "T": "Tt",

    "u": "uUûÛùÙüÜúÚūŪ",
    "U": "UuÛûÙùÜüÚúŪū",
    "û": "uUûÛùÙüÜúÚūŪ",
    "Û": "UuÛûÙùÜüÚúŪū",
    "ù": "uUûÛùÙüÜúÚūŪ",
    "Ù": "UuÛûÙùÜüÚúŪū",
    "ü": "uUûÛùÙüÜúÚūŪ",
    "Ü": "UuÛûÙùÜüÚúŪū",
    "ú": "uUûÛùÙüÜúÚūŪ",
    "Ú": "UuÛûÙùÜüÚúŪū",

    "v": "vVwW",
    "V": "VvWw",

    "w": "wWvV",
    "W": "WwVv",

    "x": "xXcCkK",
    "X": "XxCcKk",

    "y": "yYiIîÎÿŸŷŶýÝỳỲȳȲ",
    "Y": "YyIiÎîŸÿŶŷÝýỲỳȲȳ",
    "ÿ": "yYiIîÎÿŸŷŶýÝỳỲȳȲ",
    "Ÿ": "YyIiÎîŸÿŶŷÝýỲỳȲȳ",
    "ŷ": "yYiIîÎÿŸŷŶýÝỳỲȳȲ",
    "Ŷ": "YyIiÎîŸÿŶŷÝýỲỳȲȳ",
    "ý": "yYiIîÎÿŸŷŶýÝỳỲȳȲ",
    "Ý": "YyIiÎîŸÿŶŷÝýỲỳȲȳ",
    "ỳ": "yYiIîÎÿŸŷŶýÝỳỲȳȲ",
    "Ỳ": "YyIiÎîŸÿŶŷÝýỲỳȲȳ",

    "z": "zZsSẑẐźŹ",
    "Z": "ZzSsẐẑŹź",
}

d1toX = {
    "æ": ("ae",),
    "Æ": ("AE",),
    "b": ("bb",),
    "B": ("BB",),
    "c": ("cc", "ss", "qu", "ch"),
    "C": ("CC", "SS", "QU", "CH"),
    "d": ("dd",),
    "D": ("DD",),
    "é": ("ai", "ei"),
    "É": ("AI", "EI"),
    "f": ("ff", "ph"),
    "F": ("FF", "PH"),
    "g": ("gu", "ge", "gg", "gh"),
    "G": ("GU", "GE", "GG", "GH"),
    "j": ("jj", "dj"),
    "J": ("JJ", "DJ"),
    "k": ("qu", "ck", "ch", "cu", "kk", "kh"),
    "K": ("QU", "CK", "CH", "CU", "KK", "KH"),
    "l": ("ll",),
    "L": ("LL",),
    "m": ("mm", "mn"),
    "M": ("MM", "MN"),
    "n": ("nn", "nm", "mn"),
    "N": ("NN", "NM", "MN"),
    "o": ("au", "eau"),
    "O": ("AU", "EAU"),
    "œ": ("oe", "eu"),
    "Œ": ("OE", "EU"),
    "p": ("pp", "ph"),
    "P": ("PP", "PH"),
    "q": ("qu", "ch", "cq", "ck", "kk"),
    "Q": ("QU", "CH", "CQ", "CK", "KK"),
    "r": ("rr",),
    "R": ("RR",),
    "s": ("ss", "sh"),
    "S": ("SS", "SH"),
    "t": ("tt", "th"),
    "T": ("TT", "TH"),
    "x": ("cc", "ct", "xx"),
    "X": ("CC", "CT", "XX"),
    "z": ("ss", "zh"),
    "Z": ("SS", "ZH"),
}


def get1toXReplacement (cPrev, cCur, cNext):
    "return tuple of replacements for <cCur>"
    if cCur in aConsonant  and  (cPrev in aConsonant  or  cNext in aConsonant):
        return ()
    return d1toX.get(cCur, ())


d2toX = {
    "am": ("an", "en", "em"),
    "AM": ("AN", "EN", "EM"),
    "an": ("am", "en", "em"),
    "AN": ("AM", "EN", "EM"),
    "au": ("eau", "o", "ô"),
    "AU": ("EAU", "O", "Ô"),
    "em": ("an", "am", "en"),
    "EM": ("AN", "AM", "EN"),
    "en": ("an", "am", "em"),
    "EN": ("AN", "AM", "EM"),
    "ae": ("æ", "é"),
    "AE": ("Æ", "É"),
    "ai": ("ei", "é", "è", "ê", "ë"),
    "AI": ("EI", "É", "È", "Ê", "Ë"),
    "ei": ("ai", "é", "è", "ê", "ë"),
    "EI": ("AI", "É", "È", "Ê", "Ë"),
    "ch": ("sh", "c", "ss"),
    "CH": ("SH", "C", "SS"),
    "ck": ("qu", "q"),
    "CK": ("QU", "Q"),
    "ct": ("x", "cc"),
    "CT": ("X", "CC"),
    "gg": ("gu",),
    "GG": ("GU",),
    "gu": ("gg",),
    "GU": ("GG",),
    "oa": ("oi",),
    "OA": ("OI",),
    "oe": ("œ",),
    "OE": ("Œ",),
    "oi": ("oa", "oie"),
    "OI": ("OA", "OIE"),
    "ph": ("f",),
    "PH": ("F",),
    "qu": ("q", "cq", "ck", "c", "k"),
    "QU": ("Q", "CQ", "CK", "C", "K"),
    "ss": ("c", "ç"),
    "SS": ("C", "Ç"),
    "un": ("ein",),
    "UN": ("EIN",),
}


# End of word

dFinal1 = {
    "a": ("as", "at", "ant", "ah"),
    "A": ("AS", "AT", "ANT", "AH"),
    "c": ("ch",),
    "C": ("CH",),
    "e": ("et", "er", "ets", "ée", "ez", "ai", "ais", "ait", "ent", "eh"),
    "E": ("ET", "ER", "ETS", "ÉE", "EZ", "AI", "AIS", "AIT", "ENT", "EH"),
    "é": ("et", "er", "ets", "ée", "ez", "ai", "ais", "ait"),
    "É": ("ET", "ER", "ETS", "ÉE", "EZ", "AI", "AIS", "AIT"),
    "è": ("et", "er", "ets", "ée", "ez", "ai", "ais", "ait"),
    "È": ("ET", "ER", "ETS", "ÉE", "EZ", "AI", "AIS", "AIT"),
    "ê": ("et", "er", "ets", "ée", "ez", "ai", "ais", "ait"),
    "Ê": ("ET", "ER", "ETS", "ÉE", "EZ", "AI", "AIS", "AIT"),
    "ë": ("et", "er", "ets", "ée", "ez", "ai", "ais", "ait"),
    "Ë": ("ET", "ER", "ETS", "ÉE", "EZ", "AI", "AIS", "AIT"),
    "g": ("gh",),
    "G": ("GH",),
    "i": ("is", "it", "ie", "in"),
    "I": ("IS", "IT", "IE", "IN"),
    "n": ("nt", "nd", "ns", "nh"),
    "N": ("NT", "ND", "NS", "NH"),
    "o": ("aut", "ot", "os"),
    "O": ("AUT", "OT", "OS"),
    "ô": ("aut", "ot", "os"),
    "Ô": ("AUT", "OT", "OS"),
    "ö": ("aut", "ot", "os"),
    "Ö": ("AUT", "OT", "OS"),
    "p": ("ph",),
    "P": ("PH",),
    "s": ("sh",),
    "S": ("SH",),
    "t": ("th",),
    "T": ("TH",),
    "u": ("ut", "us", "uh"),
    "U": ("UT", "US", "UH"),
}

dFinal2 = {
    "ai": ("aient", "ais", "et"),
    "AI": ("AIENT", "AIS", "ET"),
    "an": ("ant", "ent"),
    "AN": ("ANT", "ENT"),
    "en": ("ent", "ant"),
    "EN": ("ENT", "ANT"),
    "ei": ("ait", "ais"),
    "EI": ("AIT", "AIS"),
    "on": ("ons", "ont"),
    "ON": ("ONS", "ONT"),
    "oi": ("ois", "oit", "oix"),
    "OI": ("OIS", "OIT", "OIX"),
}


# Préfixes et suffixes

aPfx1 = frozenset([
    "anti", "archi", "contre", "hyper", "mé", "méta", "im", "in", "ir", "par", "proto",
    "pseudo", "pré", "re", "ré", "sans", "sous", "supra", "sur", "ultra"
])
aPfx2 = frozenset([
    "belgo", "franco", "génito", "gynéco", "médico", "russo"
])


_zWordPrefixes = re.compile("(?i)^([ldmtsnjcç]|lorsqu|presqu|jusqu|puisqu|quoiqu|quelqu|qu)[’'‘`ʼ]([\\w-]+)")
_zWordSuffixes = re.compile("(?i)^(\\w+)(-(?:t-|)(?:ils?|elles?|on|je|tu|nous|vous|ce))$")

def cut (sWord):
    "returns a tuple of strings (prefix, trimed_word, suffix)"
    sPrefix = ""
    sSuffix = ""
    m = _zWordPrefixes.search(sWord)
    if m:
        sPrefix = m.group(1) + "’"
        sWord = m.group(2)
    m = _zWordSuffixes.search(sWord)
    if m:
        sWord = m.group(1)
        sSuffix = m.group(2)
    return (sPrefix, sWord, sSuffix)


# Other functions

def filterSugg (aSugg):
    "exclude suggestions"
    return filter(lambda sSugg: not sSugg.endswith(("è", "È")), aSugg)
