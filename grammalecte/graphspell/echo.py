#!python3

"""
The most boring yet indispensable function: print!
Because you can print on Windows console without being sure the script won’t crash…

Windows console don’t accept many characters.
"""

import sys


_CHARMAP = str.maketrans({  'œ': 'ö',  'Œ': 'Ö',  'ʳ': "r",  'ᵉ': "e",  'ˢ': "s",  'ᵈ': "d", '…': "_",  \
                            '“': '"',  '”': '"',  '„': '"',  '‘': "'",  '’': "'",  \
                            'ā': 'â',  'Ā': 'Â',  'ē': 'ê',  'Ē': 'Ê',  'ī': 'î',  'Ī': 'Î',  \
                            'ō': 'ô',  'Ō': 'Ô',  'ū': 'û',  'Ū': 'Û',  'Ÿ': 'Y',  \
                            'ś': 's',  'ŝ': 's',  \
                            '—': '-',  '–': '-'
                         })


def echo (obj, sep=' ', end='\n', file=sys.stdout, flush=False):
    """ Print for Windows to avoid Python crashes.
        Encoding depends on Windows locale. No useful standard.
        Always returns True (useful for debugging)."""
    if sys.platform != "win32":
        print(obj, sep=sep, end=end, file=file, flush=flush)
        return True
    try:
        print(str(obj).translate(_CHARMAP), sep=sep, end=end, file=file, flush=flush)
    except Exception:
        print(str(obj).encode('ascii', 'replace').decode('ascii', 'replace'), sep=sep, end=end, file=file, flush=flush)
    return True
