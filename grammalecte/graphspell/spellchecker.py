"""
Spellchecker.
Useful to check several dictionaries at once.

To avoid iterating over a pile of dictionaries, it is assumed that 3 are enough:
- the main dictionary, bundled with the package
- the community dictionary, added by an organization
- the personal dictionary, created by the user for its own convenience
"""

import importlib
import traceback

from . import ibdawg
from . import tokenizer


dDefaultDictionaries = {
    "fr": "fr-allvars.bdic",
    "en": "en.bdic"
}


class SpellChecker ():
    "SpellChecker: wrapper for the IBDAWG class"

    def __init__ (self, sLangCode, sfMainDic="", sfCommunityDic="", sfPersonalDic=""):
        "returns True if the main dictionary is loaded"
        self.sLangCode = sLangCode
        if not sfMainDic:
            sfMainDic = dDefaultDictionaries.get(sLangCode, "")
        self.oMainDic = self._loadDictionary(sfMainDic, True)
        self.oCommunityDic = self._loadDictionary(sfCommunityDic)
        self.oPersonalDic = self._loadDictionary(sfPersonalDic)
        self.bCommunityDic = bool(self.oCommunityDic)
        self.bPersonalDic = bool(self.oPersonalDic)
        self.oTokenizer = None
        # Default suggestions
        self.dDefaultSugg = None
        self.loadSuggestions(sLangCode)
        # storage
        self.bStorage = False
        self._dMorphologies = {}        # key: flexion, value: list of morphologies
        self._dLemmas = {}              # key: flexion, value: list of lemmas

    def _loadDictionary (self, source, bNecessary=False):
        "returns an IBDAWG object"
        if not source:
            return None
        try:
            return ibdawg.IBDAWG(source)
        except Exception as e:
            sErrorMessage = "Error [" + self.sLangCode + "]: <" + str(source) + "> not loaded."
            if bNecessary:
                raise Exception(str(e), sErrorMessage)
            print(sErrorMessage)
            traceback.print_exc()
            return None

    def _loadTokenizer (self):
        self.oTokenizer = tokenizer.Tokenizer(self.sLangCode)

    def getTokenizer (self):
        "load and return the tokenizer object"
        if not self.oTokenizer:
            self._loadTokenizer()
        return self.oTokenizer

    def setMainDictionary (self, source):
        "returns True if the dictionary is loaded"
        self.oMainDic = self._loadDictionary(source, True)
        return bool(self.oMainDic)

    def setCommunityDictionary (self, source, bActivate=True):
        "returns True if the dictionary is loaded"
        self.oCommunityDic = self._loadDictionary(source)
        self.bCommunityDic = False  if not bActivate  else bool(self.oCommunityDic)
        return bool(self.oCommunityDic)

    def setPersonalDictionary (self, source, bActivate=True):
        "returns True if the dictionary is loaded"
        self.oPersonalDic = self._loadDictionary(source)
        self.bPersonalDic = False  if not bActivate  else bool(self.oPersonalDic)
        return bool(self.oPersonalDic)

    def activateCommunityDictionary (self):
        "activate community dictionary (if available)"
        self.bCommunityDic = bool(self.oCommunityDic)

    def activatePersonalDictionary (self):
        "activate personal dictionary (if available)"
        self.bPersonalDic = bool(self.oPersonalDic)

    def deactivateCommunityDictionary (self):
        "deactivate community dictionary"
        self.bCommunityDic = False

    def deactivatePersonalDictionary (self):
        "deactivate personal dictionary"
        self.bPersonalDic = False


    # Default suggestions

    def loadSuggestions (self, sLangCode):
        "load default suggestion module for <sLangCode>"
        try:
            suggest = importlib.import_module("."+sLangCode, "grammalecte.graphspell")
        except ImportError:
            print("No suggestion module for language <"+sLangCode+">")
            return
        self.dDefaultSugg = suggest.dSugg


    # Storage

    def activateStorage (self):
        "store all lemmas and morphologies retrieved from the word graph"
        self.bStorage = True

    def deactivateStorage (self):
        "stop storing all lemmas and morphologies retrieved from the word graph"
        self.bStorage = False

    def clearStorage (self):
        "clear all stored data"
        self._dLemmas.clear()
        self._dMorphologies.clear()


    # parse text functions

    def parseParagraph (self, sText, bSpellSugg=False):
        "return a list of tokens where token value doesn’t exist in the word graph"
        if not self.oTokenizer:
            self._loadTokenizer()
        aSpellErrs = []
        for dToken in self.oTokenizer.genTokens(sText):
            if dToken['sType'] == "WORD" and not self.isValidToken(dToken['sValue']):
                if bSpellSugg:
                    dToken['aSuggestions'] = []
                    for lSugg in self.suggest(dToken['sValue']):
                        dToken['aSuggestions'].extend(lSugg)
                aSpellErrs.append(dToken)
        return aSpellErrs

    def countWordsOccurrences (self, sText, bByLemma=False, bOnlyUnknownWords=False, dWord={}):
        """count word occurrences.
           <dWord> can be used to cumulate count from several texts."""
        if not self.oTokenizer:
            self._loadTokenizer()
        for dToken in self.oTokenizer.genTokens(sText):
            if dToken['sType'].startswith("WORD"):
                if bOnlyUnknownWords:
                    if not self.isValidToken(dToken['sValue']):
                        dWord[dToken['sValue']] = dWord.get(dToken['sValue'], 0) + 1
                else:
                    if not bByLemma:
                        dWord[dToken['sValue']] = dWord.get(dToken['sValue'], 0) + 1
                    else:
                        for sLemma in self.getLemma(dToken['sValue']):
                            dWord[sLemma] = dWord.get(sLemma, 0) + 1
        return dWord

    # IBDAWG functions

    def isValidToken (self, sToken):
        "checks if sToken is valid (if there is hyphens in sToken, sToken is split, each part is checked)"
        if self.oMainDic.isValidToken(sToken):
            return True
        if self.bCommunityDic and self.oCommunityDic.isValidToken(sToken):
            return True
        if self.bPersonalDic and self.oPersonalDic.isValidToken(sToken):
            return True
        return False

    def isValid (self, sWord):
        "checks if sWord is valid (different casing tested if the first letter is a capital)"
        if self.oMainDic.isValid(sWord):
            return True
        if self.bCommunityDic and self.oCommunityDic.isValid(sWord):
            return True
        if self.bPersonalDic and self.oPersonalDic.isValid(sWord):
            return True
        return False

    def lookup (self, sWord):
        "checks if sWord is in dictionary as is (strict verification)"
        if self.oMainDic.lookup(sWord):
            return True
        if self.bCommunityDic and self.oCommunityDic.lookup(sWord):
            return True
        if self.bPersonalDic and self.oPersonalDic.lookup(sWord):
            return True
        return False

    def getMorph (self, sWord):
        "retrieves morphologies list, different casing allowed"
        if self.bStorage and sWord in self._dMorphologies:
            return self._dMorphologies[sWord]
        lMorph = self.oMainDic.getMorph(sWord)
        if self.bCommunityDic:
            lMorph.extend(self.oCommunityDic.getMorph(sWord))
        if self.bPersonalDic:
            lMorph.extend(self.oPersonalDic.getMorph(sWord))
        if self.bStorage:
            self._dMorphologies[sWord] = lMorph
            self._dLemmas[sWord] = { s[1:s.find("/")]  for s in lMorph }
        return lMorph

    def getLemma (self, sWord):
        "retrieves lemmas"
        if self.bStorage:
            if sWord not in self._dLemmas:
                self.getMorph(sWord)
            return self._dLemmas[sWord]
        return { s[1:s.find("/")]  for s in self.getMorph(sWord) }

    def suggest (self, sWord, nSuggLimit=10):
        "generator: returns 1, 2 or 3 lists of suggestions"
        if self.dDefaultSugg:
            if sWord in self.dDefaultSugg:
                yield self.dDefaultSugg[sWord].split("|")
            elif sWord.istitle() and sWord.lower() in self.dDefaultSugg:
                lRes = self.dDefaultSugg[sWord.lower()].split("|")
                yield list(map(lambda sSugg: sSugg[0:1].upper()+sSugg[1:], lRes))
            else:
                yield self.oMainDic.suggest(sWord, nSuggLimit, True)
        else:
            yield self.oMainDic.suggest(sWord, nSuggLimit, True)
        if self.bCommunityDic:
            yield self.oCommunityDic.suggest(sWord, (nSuggLimit//2)+1)
        if self.bPersonalDic:
            yield self.oPersonalDic.suggest(sWord, (nSuggLimit//2)+1)

    def select (self, sFlexPattern="", sTagsPattern=""):
        "generator: returns all entries which flexion fits <sFlexPattern> and morphology fits <sTagsPattern>"
        yield from self.oMainDic.select(sFlexPattern, sTagsPattern)
        if self.bCommunityDic:
            yield from self.oCommunityDic.select(sFlexPattern, sTagsPattern)
        if self.bPersonalDic:
            yield from self.oPersonalDic.select(sFlexPattern, sTagsPattern)

    def drawPath (self, sWord):
        "draw the path taken by <sWord> within the word graph: display matching nodes and their arcs"
        self.oMainDic.drawPath(sWord)
        if self.bCommunityDic:
            print("-----")
            self.oCommunityDic.drawPath(sWord)
        if self.bPersonalDic:
            print("-----")
            self.oPersonalDic.drawPath(sWord)

    def getSimilarEntries (self, sWord, nSuggLimit=10):
        "return a list of tuples (similar word, stem, morphology)"
        lResult = self.oMainDic.getSimilarEntries(sWord, nSuggLimit)
        if self.bCommunityDic:
            lResult.extend(self.oCommunityDic.getSimilarEntries(sWord, nSuggLimit))
        if self.bPersonalDic:
            lResult.extend(self.oPersonalDic.getSimilarEntries(sWord, nSuggLimit))
        return lResult
