"""
Grammalecte - Lexicographe
"""

# License: MPL 2


import re
import traceback


_dTAGS = {
    ':N': (" nom,", "Nom"),
    ':A': (" adjectif,", "Adjectif"),
    ':M1': (" prénom,", "Prénom"),
    ':M2': (" patronyme,", "Patronyme, matronyme, nom de famille…"),
    ':MP': (" nom propre,", "Nom propre"),
    ':W': (" adverbe,", "Adverbe"),
    ':J': (" interjection,", "Interjection"),
    ':B': (" nombre,", "Nombre"),
    ':T': (" titre,", "Titre de civilité"),

    ':e': (" épicène", "épicène"),
    ':m': (" masculin", "masculin"),
    ':f': (" féminin", "féminin"),
    ':s': (" singulier", "singulier"),
    ':p': (" pluriel", "pluriel"),
    ':i': (" invariable", "invariable"),

    ':V1': (" verbe (1ᵉʳ gr.),", "Verbe du 1ᵉʳ groupe"),
    ':V2': (" verbe (2ᵉ gr.),", "Verbe du 2ᵉ groupe"),
    ':V3': (" verbe (3ᵉ gr.),", "Verbe du 3ᵉ groupe"),
    ':V0e': (" verbe,", "Verbe auxiliaire être"),
    ':V0a': (" verbe,", "Verbe auxiliaire avoir"),

    ':Y': (" infinitif,", "infinitif"),
    ':P': (" participe présent,", "participe présent"),
    ':Q': (" participe passé,", "participe passé"),
    ':Ip': (" présent,", "indicatif présent"),
    ':Iq': (" imparfait,", "indicatif imparfait"),
    ':Is': (" passé simple,", "indicatif passé simple"),
    ':If': (" futur,", "indicatif futur"),
    ':K': (" conditionnel présent,", "conditionnel présent"),
    ':Sp': (" subjonctif présent,", "subjonctif présent"),
    ':Sq': (" subjonctif imparfait,", "subjonctif imparfait"),
    ':E': (" impératif,", "impératif"),

    ':1s': (" 1ʳᵉ p. sg.,", "verbe : 1ʳᵉ personne du singulier"),
    ':1ŝ': (" présent interr. 1ʳᵉ p. sg.,", "verbe : 1ʳᵉ personne du singulier (présent interrogatif)"),
    ':1ś': (" présent interr. 1ʳᵉ p. sg.,", "verbe : 1ʳᵉ personne du singulier (présent interrogatif)"),
    ':2s': (" 2ᵉ p. sg.,", "verbe : 2ᵉ personne du singulier"),
    ':3s': (" 3ᵉ p. sg.,", "verbe : 3ᵉ personne du singulier"),
    ':1p': (" 1ʳᵉ p. pl.,", "verbe : 1ʳᵉ personne du pluriel"),
    ':2p': (" 2ᵉ p. pl.,", "verbe : 2ᵉ personne du pluriel"),
    ':3p': (" 3ᵉ p. pl.,", "verbe : 3ᵉ personne du pluriel"),
    ':3p!': (" 3ᵉ p. pl.,", "verbe : 3ᵉ personne du pluriel (prononciation distinctive)"),

    ':G': ("", "Mot grammatical"),
    ':X': (" adverbe de négation,", "Adverbe de négation"),
    ':U': (" adverbe interrogatif,", "Adverbe interrogatif"),
    ':R': (" préposition,", "Préposition"),
    ':Rv': (" préposition verbale,", "Préposition verbale"),
    ':D': (" déterminant,", "Déterminant"),
    ':Dd': (" déterminant démonstratif,", "Déterminant démonstratif"),
    ':De': (" déterminant exclamatif,", "Déterminant exclamatif"),
    ':Dp': (" déterminant possessif,", "Déterminant possessif"),
    ':Di': (" déterminant indéfini,", "Déterminant indéfini"),
    ':Dn': (" déterminant négatif,", "Déterminant négatif"),
    ':Od': (" pronom démonstratif,", "Pronom démonstratif"),
    ':Oi': (" pronom indéfini,", "Pronom indéfini"),
    ':On': (" pronom indéfini négatif,", "Pronom indéfini négatif"),
    ':Ot': (" pronom interrogatif,", "Pronom interrogatif"),
    ':Or': (" pronom relatif,", "Pronom relatif"),
    ':Ow': (" pronom adverbial,", "Pronom adverbial"),
    ':Os': (" pronom personnel sujet,", "Pronom personnel sujet"),
    ':Oo': (" pronom personnel objet,", "Pronom personnel objet"),
    ':Ov': (" préverbe,", "Préverbe (pronom personnel objet, +ne)"),
    ':O1': (" 1ʳᵉ pers.,", "Pronom : 1ʳᵉ personne"),
    ':O2': (" 2ᵉ pers.,", "Pronom : 2ᵉ personne"),
    ':O3': (" 3ᵉ pers.,", "Pronom : 3ᵉ personne"),
    ':C': (" conjonction,", "Conjonction"),
    ':Ĉ': (" conjonction (él.),", "Conjonction (élément)"),
    ':Cc': (" conjonction de coordination,", "Conjonction de coordination"),
    ':Cs': (" conjonction de subordination,", "Conjonction de subordination"),
    ':Ĉs': (" conjonction de subordination (él.),", "Conjonction de subordination (élément)"),

    ':Ñ': (" locution nominale (él.),", "Locution nominale (élément)"),
    ':Â': (" locution adjectivale (él.),", "Locution adjectivale (élément)"),
    ':Ṽ': (" locution verbale (él.),", "Locution verbale (élément)"),
    ':Ŵ': (" locution adverbiale (él.),", "Locution adverbiale (élément)"),
    ':Ŕ': (" locution prépositive (él.),", "Locution prépositive (élément)"),
    ':Ĵ': (" locution interjective (él.),", "Locution interjective (élément)"),

    ':Zp': (" préfixe,", "Préfixe"),
    ':Zs': (" suffixe,", "Suffixe"),

    ':H': ("", "<Hors-norme, inclassable>"),

    ':@': ("", "<Caractère non alpha-numérique>"),
    ':@p': ("signe de ponctuation", "Signe de ponctuation"),
    ':@s': ("signe", "Signe divers"),

    ';S': (" : symbole (unité de mesure)", "Symbole (unité de mesure)"),

    '/*': ("", "Sous-dictionnaire <Commun>"),
    '/C': (" <classique>", "Sous-dictionnaire <Classique>"),
    '/M': ("", "Sous-dictionnaire <Moderne>"),
    '/R': (" <réforme>", "Sous-dictionnaire <Réforme 1990>"),
    '/A': ("", "Sous-dictionnaire <Annexe>"),
    '/X': ("", "Sous-dictionnaire <Contributeurs>")
}

_dPFX = {
    'd': "(de), déterminant épicène invariable",
    'l': "(le/la), déterminant masculin/féminin singulier",
    'j': "(je), pronom personnel sujet, 1ʳᵉ pers., épicène singulier",
    'm': "(me), pronom personnel objet, 1ʳᵉ pers., épicène singulier",
    't': "(te), pronom personnel objet, 2ᵉ pers., épicène singulier",
    's': "(se), pronom personnel objet, 3ᵉ pers., épicène singulier/pluriel",
    'n': "(ne), adverbe de négation",
    'c': "(ce), pronom démonstratif, masculin singulier/pluriel",
    'ç': "(ça), pronom démonstratif, masculin singulier",
    'qu': "(que), conjonction de subordination",
    'lorsqu': "(lorsque), conjonction de subordination",
    'puisqu': "(puisque), conjonction de subordination",
    'quoiqu': "(quoique), conjonction de subordination",
    'jusqu': "(jusque), préposition",
}

_dAD = {
    'je': " pronom personnel sujet, 1ʳᵉ pers. sing.",
    'tu': " pronom personnel sujet, 2ᵉ pers. sing.",
    'il': " pronom personnel sujet, 3ᵉ pers. masc. sing.",
    'on': " pronom personnel sujet, 3ᵉ pers. sing. ou plur.",
    'elle': " pronom personnel sujet, 3ᵉ pers. fém. sing.",
    'nous': " pronom personnel sujet/objet, 1ʳᵉ pers. plur.",
    'vous': " pronom personnel sujet/objet, 2ᵉ pers. plur.",
    'ils': " pronom personnel sujet, 3ᵉ pers. masc. plur.",
    'elles': " pronom personnel sujet, 3ᵉ pers. masc. plur.",

    "là": " particule démonstrative",
    "ci": " particule démonstrative",

    'le': " COD, masc. sing.",
    'la': " COD, fém. sing.",
    'les': " COD, plur.",

    'moi': " COI (à moi), sing.",
    'toi': " COI (à toi), sing.",
    'lui': " COI (à lui ou à elle), sing.",
    'nous2': " COI (à nous), plur.",
    'vous2': " COI (à vous), plur.",
    'leur': " COI (à eux ou à elles), plur.",

    'y': " pronom adverbial",
    "m'y": " (me) pronom personnel objet + (y) pronom adverbial",
    "t'y": " (te) pronom personnel objet + (y) pronom adverbial",
    "s'y": " (se) pronom personnel objet + (y) pronom adverbial",

    'en': " pronom adverbial",
    "m'en": " (me) pronom personnel objet + (en) pronom adverbial",
    "t'en": " (te) pronom personnel objet + (en) pronom adverbial",
    "s'en": " (se) pronom personnel objet + (en) pronom adverbial",
}


class Lexicographe:
    "Lexicographer - word analyzer"

    def __init__ (self, oSpellChecker):
        self.oSpellChecker = oSpellChecker
        self._zElidedPrefix = re.compile("(?i)^([dljmtsncç]|quoiqu|lorsqu|jusqu|puisqu|qu)['’](.+)")
        self._zCompoundWord = re.compile("(?i)(\\w+)-((?:les?|la)-(?:moi|toi|lui|[nv]ous|leur)|t-(?:il|elle|on)|y|en|[mts][’'](?:y|en)|les?|l[aà]|[mt]oi|leur|lui|je|tu|ils?|elles?|on|[nv]ous)$")
        self._zTag = re.compile("[:;/][\\w*][^:;/]*")

    def analyzeWord (self, sWord):
        "returns a tuple (a list of morphologies, a set of verb at infinitive form)"
        try:
            if not sWord:
                return (None, None)
            if sWord.count("-") > 4:
                return (["élément complexe indéterminé"], None)
            if sWord.isdigit():
                return (["nombre"], None)

            aMorph = []
            # préfixes élidés
            m = self._zElidedPrefix.match(sWord)
            if m:
                sWord = m.group(2)
                aMorph.append( "{}’ : {}".format(m.group(1), _dPFX.get(m.group(1).lower(), "[?]")) )
            # mots composés
            m2 = self._zCompoundWord.match(sWord)
            if m2:
                sWord = m2.group(1)
            # Morphologies
            lMorph = self.oSpellChecker.getMorph(sWord)
            if len(lMorph) > 1:
                # sublist
                aMorph.append( (sWord, [ self.formatTags(s)  for s in lMorph  if ":" in s ]) )
            elif len(lMorph) == 1:
                aMorph.append( "{} : {}".format(sWord, self.formatTags(lMorph[0])) )
            else:
                aMorph.append( "{} :  inconnu du dictionnaire".format(sWord) )
            # suffixe d’un mot composé
            if m2:
                aMorph.append( "-{} : {}".format(m2.group(2), self._formatSuffix(m2.group(2).lower())) )
            # Verbes
            aVerb = { s[1:s.find("/")]  for s in lMorph  if ":V" in s }
            return (aMorph, aVerb)
        except (IndexError, TypeError):
            traceback.print_exc()
            return (["#erreur"], None)

    def formatTags (self, sTags):
        "returns string: readable tags"
        sRes = ""
        sTags = re.sub("(?<=V[1-3])[itpqnmr_eaxz]+", "", sTags)
        sTags = re.sub("(?<=V0[ea])[itpqnmr_eaxz]+", "", sTags)
        for m in self._zTag.finditer(sTags):
            sRes += _dTAGS.get(m.group(0), " [{}]".format(m.group(0)))[0]
        if sRes.startswith(" verbe") and not sRes.endswith("infinitif"):
            sRes += " [{}]".format(sTags[1:sTags.find("/")])
        return sRes.rstrip(",")

    def _formatSuffix (self, s):
        if s.startswith("t-"):
            return "“t” euphonique +" + _dAD.get(s[2:], "[?]")
        if not "-" in s:
            return _dAD.get(s.replace("’", "'"), "[?]")
        if s.endswith("ous"):
            s += '2'
        nPos = s.find("-")
        return "%s +%s" % (_dAD.get(s[:nPos], "[?]"), _dAD.get(s[nPos+1:], "[?]"))
