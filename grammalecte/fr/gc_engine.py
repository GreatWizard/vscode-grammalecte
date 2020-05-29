"""
Grammalecte
Grammar checker engine
"""

import re
import traceback
#import unicodedata
from itertools import chain

from ..graphspell.spellchecker import SpellChecker
from ..graphspell.echo import echo

from .. import text

from . import gc_options

try:
    # LibreOffice / OpenOffice
    from com.sun.star.linguistic2 import SingleProofreadingError
    from com.sun.star.text.TextMarkupType import PROOFREADING
    from com.sun.star.beans import PropertyValue
    #import lightproof_handler_grammalecte as opt
    _bWriterError = True
except ImportError:
    _bWriterError = False


__all__ = [ "lang", "locales", "pkg", "name", "version", "author", \
            "load", "parse", "getSpellChecker", \
            "setOption", "setOptions", "getOptions", "getDefaultOptions", "getOptionsLabels", "resetOptions", "displayOptions", \
            "ignoreRule", "resetIgnoreRules", "reactivateRule", "listRules", "displayRules", "setWriterUnderliningStyle" ]

__version__ = "1.9.0"


lang = "fr"
locales = {'fr-FR': ['fr', 'FR', ''], 'fr-BE': ['fr', 'BE', ''], 'fr-CA': ['fr', 'CA', ''], 'fr-CH': ['fr', 'CH', ''], 'fr-LU': ['fr', 'LU', ''], 'fr-BF': ['fr', 'BF', ''], 'fr-BJ': ['fr', 'BJ', ''], 'fr-CD': ['fr', 'CD', ''], 'fr-CI': ['fr', 'CI', ''], 'fr-CM': ['fr', 'CM', ''], 'fr-MA': ['fr', 'MA', ''], 'fr-ML': ['fr', 'ML', ''], 'fr-MU': ['fr', 'MU', ''], 'fr-NE': ['fr', 'NE', ''], 'fr-RE': ['fr', 'RE', ''], 'fr-SN': ['fr', 'SN', ''], 'fr-TG': ['fr', 'TG', '']}
pkg = "grammalecte"
name = "Grammalecte"
version = "1.9.0"
author = "Olivier R."

# Modules
_rules = None                               # module gc_rules
_rules_graph = None                         # module gc_rules_graph

# Data
_sAppContext = ""                           # what software is running
_dOptions = None
_dOptionsColors = None
_oSpellChecker = None
_oTokenizer = None
_aIgnoredRules = set()

# Writer underlining style
_bMulticolor = True
_nUnderliningStyle = 0


#### Initialization

def load (sContext="Python", sColorType="aRGB"):
    "initialization of the grammar checker"
    global _oSpellChecker
    global _sAppContext
    global _dOptions
    global _dOptionsColors
    global _oTokenizer
    try:
        _oSpellChecker = SpellChecker("fr", "fr-allvars.bdic", "", "")
        _sAppContext = sContext
        _dOptions = gc_options.getOptions(sContext).copy()   # duplication necessary, to be able to reset to default
        _dOptionsColors = gc_options.getOptionsColors(sContext, sColorType)
        _oTokenizer = _oSpellChecker.getTokenizer()
        _oSpellChecker.activateStorage()
    except:
        traceback.print_exc()


def getSpellChecker ():
    "return the spellchecker object"
    return _oSpellChecker


#### Rules

def _getRules (bParagraph):
    try:
        if not bParagraph:
            return _rules.lSentenceRules
        return _rules.lParagraphRules
    except:
        _loadRules()
    if not bParagraph:
        return _rules.lSentenceRules
    return _rules.lParagraphRules


def _loadRules ():
    from . import gc_rules
    from . import gc_rules_graph
    global _rules
    global _rules_graph
    _rules = gc_rules
    _rules_graph = gc_rules_graph
    # compile rules regex
    for sOption, lRuleGroup in chain(_rules.lParagraphRules, _rules.lSentenceRules):
        if sOption != "@@@@":
            for aRule in lRuleGroup:
                try:
                    aRule[0] = re.compile(aRule[0])
                except (IndexError, re.error):
                    echo("Bad regular expression in # " + str(aRule[2]))
                    aRule[0] = "(?i)<Grammalecte>"


def ignoreRule (sRuleId):
    "disable rule <sRuleId>"
    _aIgnoredRules.add(sRuleId)


def resetIgnoreRules ():
    "clear all ignored rules"
    _aIgnoredRules.clear()


def reactivateRule (sRuleId):
    "(re)activate rule <sRuleId>"
    _aIgnoredRules.discard(sRuleId)


def listRules (sFilter=None):
    "generator: returns typle (sOption, sLineId, sRuleId)"
    if sFilter:
        try:
            zFilter = re.compile(sFilter)
        except re.error:
            echo("# Error. List rules: wrong regex.")
            sFilter = None
    # regex rules
    for sOption, lRuleGroup in chain(_getRules(True), _getRules(False)):
        if sOption != "@@@@":
            for _, _, sLineId, sRuleId, _, _ in lRuleGroup:
                if not sFilter or zFilter.search(sRuleId):
                    yield ("RegEx", sOption, sLineId, sRuleId)
    # tokens rules
    for sRuleName, lActions in _rules_graph.dRule.items():
        sLineId, sOption, _, cActionType, *_ = lActions
        if cActionType == "-":
            yield("Tokens", sOption, sLineId, sRuleName)


def displayRules (sFilter=None):
    "display the name of rules, with the filter <sFilter>"
    echo("List of rules. Filter: << " + str(sFilter) + " >>")
    for sOption, sLineId, sRuleId, sType in listRules(sFilter):
        echo("{:<8} {:<10} {:<10} {}".format(sOption, sLineId, sRuleId, sType))


#### Options

def setOption (sOpt, bVal):
    "set option <sOpt> with <bVal> if it exists"
    if sOpt in _dOptions:
        _dOptions[sOpt] = bVal


def setOptions (dOpt):
    "update the dictionary of options with <dOpt>"
    for sKey, bVal in dOpt.items():
        if sKey in _dOptions:
            _dOptions[sKey] = bVal


def getOptions ():
    "return the dictionary of current options"
    return _dOptions


def getDefaultOptions ():
    "return the dictionary of default options"
    return gc_options.getOptions(_sAppContext).copy()


def getOptionsLabels (sLang):
    "return options labels"
    return gc_options.getUI(sLang)


def displayOptions (sLang="fr"):
    "display the list of grammar checking options"
    echo("Options:")
    echo("\n".join( [ k+":\t"+str(v)+"\t"+gc_options.getUI(sLang).get(k, ("?", ""))[0]  for k, v  in sorted(_dOptions.items()) ] ))
    echo("")


def resetOptions ():
    "set options to default values"
    global _dOptions
    _dOptions = getDefaultOptions()


def setWriterUnderliningStyle (sStyle="BOLDWAVE", bMulticolor=True):
    "set underlining style for Writer (WAVE, BOLDWAVE, BOLD)"
    global _nUnderliningStyle
    global _bMulticolor
    # https://api.libreoffice.org/docs/idl/ref/FontUnderline_8idl.html
    # WAVE: 10, BOLD: 12, BOLDWAVE: 18 DASH: 5
    if sStyle == "WAVE":
        _nUnderliningStyle = 0  # 0 for default Writer setting
    elif sStyle == "BOLDWAVE":
        _nUnderliningStyle = 18
    elif sStyle == "BOLD":
        _nUnderliningStyle = 12
    elif sStyle == "DASH":
        _nUnderliningStyle = 5
    else:
        _nUnderliningStyle = 0
    _bMulticolor = bMulticolor


#### Parsing

def parse (sText, sCountry="FR", bDebug=False, dOptions=None, bContext=False, bFullInfo=False):
    "init point to analyse <sText> and returns an iterable of errors or (with option <bFullInfo>) paragraphs errors and sentences with tokens and errors"
    oText = TextParser(sText)
    return oText.parse(sCountry, bDebug, dOptions, bContext, bFullInfo)


#### TEXT PARSER

class TextParser:
    "Text parser"

    def __init__ (self, sText):
        self.sText = sText
        self.sText0 = sText
        self.sSentence = ""
        self.sSentence0 = ""
        self.nOffsetWithinParagraph = 0
        self.lToken = []
        self.dTokenPos = {}         # {position: token}
        self.dTags = {}             # {position: tags}
        self.dError = {}            # {position: error}
        self.dSentenceError = {}    # {position: error} (for the current sentence only)
        self.dErrorPriority = {}    # {position: priority of the current error}

    def __str__ (self):
        s = "===== TEXT =====\n"
        s += "sentence: " + self.sSentence0 + "\n"
        s += "now:      " + self.sSentence  + "\n"
        for dToken in self.lToken:
            s += '#{i}\t{nStart}:{nEnd}\t{sValue}\t{sType}'.format(**dToken)
            if "lMorph" in dToken:
                s += "\t" + str(dToken["lMorph"])
            if "aTags" in dToken:
                s += "\t" + str(dToken["aTags"])
            s += "\n"
        #for nPos, dToken in self.dTokenPos.items():
        #    s += "{}\t{}\n".format(nPos, dToken)
        return s

    def parse (self, sCountry="FR", bDebug=False, dOptions=None, bContext=False, bFullInfo=False):
        "analyses <sText> and returns an iterable of errors or (with option <bFullInfo>) paragraphs errors and sentences with tokens and errors"
        #sText = unicodedata.normalize("NFC", sText)
        dOpt = dOptions or _dOptions
        bShowRuleId = option('idrule')
        # parse paragraph
        try:
            self.parseText(self.sText, self.sText0, True, 0, sCountry, dOpt, bShowRuleId, bDebug, bContext)
        except:
            raise
        if bFullInfo:
            lParagraphErrors = list(self.dError.values())
            lSentences = []
            self.dSentenceError.clear()
        # parse sentences
        sText = self._getCleanText()
        for iStart, iEnd in text.getSentenceBoundaries(sText):
            if 4 < (iEnd - iStart) < 2000:
                try:
                    self.sSentence = sText[iStart:iEnd]
                    self.sSentence0 = self.sText0[iStart:iEnd]
                    self.nOffsetWithinParagraph = iStart
                    self.lToken = list(_oTokenizer.genTokens(self.sSentence, True))
                    self.dTokenPos = { dToken["nStart"]: dToken  for dToken in self.lToken  if dToken["sType"] != "INFO" }
                    if bFullInfo:
                        dSentence = { "nStart": iStart, "nEnd": iEnd, "sSentence": self.sSentence, "lToken": list(self.lToken) }
                        for dToken in dSentence["lToken"]:
                            if dToken["sType"] == "WORD":
                                dToken["bValidToken"] = _oSpellChecker.isValidToken(dToken["sValue"])
                        # the list of tokens is duplicated, to keep all tokens from being deleted when analysis
                    self.parseText(self.sSentence, self.sSentence0, False, iStart, sCountry, dOpt, bShowRuleId, bDebug, bContext)
                    if bFullInfo:
                        dSentence["lGrammarErrors"] = list(self.dSentenceError.values())
                        lSentences.append(dSentence)
                        self.dSentenceError.clear()
                except:
                    raise
        if bFullInfo:
            # Grammar checking and sentence analysis
            return lParagraphErrors, lSentences
        else:
            # Grammar checking only
            return self.dError.values() # this is a view (iterable)

    def _getCleanText (self):
        sText = self.sText
        if " " in sText:
            sText = sText.replace(" ", ' ') # nbsp
        if " " in sText:
            sText = sText.replace(" ", ' ') # nnbsp
        if "'" in sText:
            sText = sText.replace("'", "’")
        if "‑" in sText:
            sText = sText.replace("‑", "-") # nobreakdash
        if "@@" in sText:
            sText = re.sub("@@+", "", sText)
        return sText

    def parseText (self, sText, sText0, bParagraph, nOffset, sCountry, dOptions, bShowRuleId, bDebug, bContext):
        "parse the text with rules"
        bChange = False
        for sOption, lRuleGroup in _getRules(bParagraph):
            if sOption == "@@@@":
                # graph rules
                if not bParagraph and bChange:
                    self.update(sText, bDebug)
                    bChange = False
                for sGraphName, sLineId in lRuleGroup:
                    if sGraphName not in dOptions or dOptions[sGraphName]:
                        if bDebug:
                            echo("\n>>>> GRAPH: " + sGraphName + " " + sLineId)
                        sText = self.parseGraph(_rules_graph.dAllGraph[sGraphName], sCountry, dOptions, bShowRuleId, bDebug, bContext)
            elif not sOption or dOptions.get(sOption, False):
                # regex rules
                for zRegex, bUppercase, sLineId, sRuleId, nPriority, lActions in lRuleGroup:
                    if sRuleId not in _aIgnoredRules:
                        for m in zRegex.finditer(sText):
                            bCondMemo = None
                            for sFuncCond, cActionType, sWhat, *eAct in lActions:
                                # action in lActions: [ condition, action type, replacement/suggestion/action[, iGroup[, message, URL]] ]
                                try:
                                    bCondMemo = not sFuncCond or globals()[sFuncCond](sText, sText0, m, self.dTokenPos, sCountry, bCondMemo)
                                    if bCondMemo:
                                        if bDebug:
                                            echo("RULE: " + sLineId)
                                        if cActionType == "-":
                                            # grammar error
                                            nErrorStart = nOffset + m.start(eAct[0])
                                            if nErrorStart not in self.dError or nPriority > self.dErrorPriority.get(nErrorStart, -1):
                                                self.dError[nErrorStart] = self._createErrorFromRegex(sText, sText0, sWhat, nOffset, m, eAct[0], sLineId, sRuleId, bUppercase, eAct[1], eAct[2], bShowRuleId, sOption, bContext)
                                                self.dErrorPriority[nErrorStart] = nPriority
                                                self.dSentenceError[nErrorStart] = self.dError[nErrorStart]
                                        elif cActionType == "~":
                                            # text processor
                                            sText = self.rewriteText(sText, sWhat, eAct[0], m, bUppercase)
                                            bChange = True
                                            if bDebug:
                                                echo("~ " + sText + "  -- " + m.group(eAct[0]) + "  # " + sLineId)
                                        elif cActionType == "=":
                                            # disambiguation
                                            if not bParagraph:
                                                globals()[sWhat](sText, m, self.dTokenPos)
                                                if bDebug:
                                                    echo("= " + m.group(0) + "  # " + sLineId)
                                        elif cActionType == ">":
                                            # we do nothing, this test is just a condition to apply all following actions
                                            pass
                                        else:
                                            echo("# error: unknown action at " + sLineId)
                                    elif cActionType == ">":
                                        break
                                except Exception as e:
                                    raise Exception(str(e), "# " + sLineId + " # " + sRuleId)
        if bChange:
            if bParagraph:
                self.sText = sText
            else:
                self.sSentence = sText

    def update (self, sSentence, bDebug=False):
        "update <sSentence> and retokenize"
        self.sSentence = sSentence
        lNewToken = list(_oTokenizer.genTokens(sSentence, True))
        for dToken in lNewToken:
            if "lMorph" in self.dTokenPos.get(dToken["nStart"], {}):
                dToken["lMorph"] = self.dTokenPos[dToken["nStart"]]["lMorph"]
            if "aTags" in self.dTokenPos.get(dToken["nStart"], {}):
                dToken["aTags"] = self.dTokenPos[dToken["nStart"]]["aTags"]
        self.lToken = lNewToken
        self.dTokenPos = { dToken["nStart"]: dToken  for dToken in self.lToken  if dToken["sType"] != "INFO" }
        if bDebug:
            echo("UPDATE:")
            echo(self)

    def _getNextPointers (self, dToken, dGraph, dPointer, bDebug=False):
        "generator: return nodes where <dToken> “values” match <dNode> arcs"
        dNode = dGraph[dPointer["iNode"]]
        iToken1 = dPointer["iToken1"]
        bTokenFound = False
        # token value
        if dToken["sValue"] in dNode:
            if bDebug:
                echo("  MATCH: " + dToken["sValue"])
            yield { "iToken1": iToken1, "iNode": dNode[dToken["sValue"]] }
            bTokenFound = True
        if dToken["sValue"][0:2].istitle(): # we test only 2 first chars, to make valid words such as "Laissez-les", "Passe-partout".
            sValue = dToken["sValue"].lower()
            if sValue in dNode:
                if bDebug:
                    echo("  MATCH: " + sValue)
                yield { "iToken1": iToken1, "iNode": dNode[sValue] }
                bTokenFound = True
        elif dToken["sValue"].isupper():
            sValue = dToken["sValue"].lower()
            if sValue in dNode:
                if bDebug:
                    echo("  MATCH: " + sValue)
                yield { "iToken1": iToken1, "iNode": dNode[sValue] }
                bTokenFound = True
            sValue = dToken["sValue"].capitalize()
            if sValue in dNode:
                if bDebug:
                    echo("  MATCH: " + sValue)
                yield { "iToken1": iToken1, "iNode": dNode[sValue] }
                bTokenFound = True
        # regex value arcs
        if dToken["sType"] not in frozenset(["INFO", "PUNC", "SIGN"]):
            if "<re_value>" in dNode:
                for sRegex in dNode["<re_value>"]:
                    if "¬" not in sRegex:
                        # no anti-pattern
                        if re.search(sRegex, dToken["sValue"]):
                            if bDebug:
                                echo("  MATCH: ~" + sRegex)
                            yield { "iToken1": iToken1, "iNode": dNode["<re_value>"][sRegex] }
                            bTokenFound = True
                    else:
                        # there is an anti-pattern
                        sPattern, sNegPattern = sRegex.split("¬", 1)
                        if sNegPattern and re.search(sNegPattern, dToken["sValue"]):
                            continue
                        if not sPattern or re.search(sPattern, dToken["sValue"]):
                            if bDebug:
                                echo("  MATCH: ~" + sRegex)
                            yield { "iToken1": iToken1, "iNode": dNode["<re_value>"][sRegex] }
                            bTokenFound = True
        # analysable tokens
        if dToken["sType"][0:4] == "WORD":
            # token lemmas
            if "<lemmas>" in dNode:
                for sLemma in _oSpellChecker.getLemma(dToken["sValue"]):
                    if sLemma in dNode["<lemmas>"]:
                        if bDebug:
                            echo("  MATCH: >" + sLemma)
                        yield { "iToken1": iToken1, "iNode": dNode["<lemmas>"][sLemma] }
                        bTokenFound = True
            # morph arcs
            if "<morph>" in dNode:
                lMorph = dToken.get("lMorph", _oSpellChecker.getMorph(dToken["sValue"]))
                if lMorph:
                    for sSearch in dNode["<morph>"]:
                        if "¬" not in sSearch:
                            # no anti-pattern
                            if any(sSearch in sMorph  for sMorph in lMorph):
                                if bDebug:
                                    echo("  MATCH: $" + sSearch)
                                yield { "iToken1": iToken1, "iNode": dNode["<morph>"][sSearch] }
                                bTokenFound = True
                        else:
                            # there is an anti-pattern
                            sPattern, sNegPattern = sSearch.split("¬", 1)
                            if sNegPattern == "*":
                                # all morphologies must match with <sPattern>
                                if sPattern:
                                    if all(sPattern in sMorph  for sMorph in lMorph):
                                        if bDebug:
                                            echo("  MATCH: $" + sSearch)
                                        yield { "iToken1": iToken1, "iNode": dNode["<morph>"][sSearch] }
                                        bTokenFound = True
                            else:
                                if sNegPattern and any(sNegPattern in sMorph  for sMorph in lMorph):
                                    continue
                                if not sPattern or any(sPattern in sMorph  for sMorph in lMorph):
                                    if bDebug:
                                        echo("  MATCH: $" + sSearch)
                                    yield { "iToken1": iToken1, "iNode": dNode["<morph>"][sSearch] }
                                    bTokenFound = True
            # regex morph arcs
            if "<re_morph>" in dNode:
                lMorph = dToken.get("lMorph", _oSpellChecker.getMorph(dToken["sValue"]))
                if lMorph:
                    for sRegex in dNode["<re_morph>"]:
                        if "¬" not in sRegex:
                            # no anti-pattern
                            if any(re.search(sRegex, sMorph)  for sMorph in lMorph):
                                if bDebug:
                                    echo("  MATCH: @" + sRegex)
                                yield { "iToken1": iToken1, "iNode": dNode["<re_morph>"][sRegex] }
                                bTokenFound = True
                        else:
                            # there is an anti-pattern
                            sPattern, sNegPattern = sRegex.split("¬", 1)
                            if sNegPattern == "*":
                                # all morphologies must match with <sPattern>
                                if sPattern:
                                    if all(re.search(sPattern, sMorph)  for sMorph in lMorph):
                                        if bDebug:
                                            echo("  MATCH: @" + sRegex)
                                        yield { "iToken1": iToken1, "iNode": dNode["<re_morph>"][sRegex] }
                                        bTokenFound = True
                            else:
                                if sNegPattern and any(re.search(sNegPattern, sMorph)  for sMorph in lMorph):
                                    continue
                                if not sPattern or any(re.search(sPattern, sMorph)  for sMorph in lMorph):
                                    if bDebug:
                                        echo("  MATCH: @" + sRegex)
                                    yield { "iToken1": iToken1, "iNode": dNode["<re_morph>"][sRegex] }
                                    bTokenFound = True
        # token tags
        if "aTags" in dToken and "<tags>" in dNode:
            for sTag in dToken["aTags"]:
                if sTag in dNode["<tags>"]:
                    if bDebug:
                        echo("  MATCH: /" + sTag)
                    yield { "iToken1": iToken1, "iNode": dNode["<tags>"][sTag] }
                    bTokenFound = True
        # meta arc (for token type)
        if "<meta>" in dNode:
            for sMeta in dNode["<meta>"]:
                # no regex here, we just search if <dNode["sType"]> exists within <sMeta>
                if sMeta == "*" or dToken["sType"] == sMeta:
                    if bDebug:
                        echo("  MATCH: *" + sMeta)
                    yield { "iToken1": iToken1, "iNode": dNode["<meta>"][sMeta] }
                    bTokenFound = True
                elif "¬" in sMeta:
                    if dToken["sType"] not in sMeta:
                        if bDebug:
                            echo("  MATCH: *" + sMeta)
                        yield { "iToken1": iToken1, "iNode": dNode["<meta>"][sMeta] }
                        bTokenFound = True
        if not bTokenFound and "bKeep" in dPointer:
            yield dPointer
        # JUMP
        # Warning! Recurssion!
        if "<>" in dNode:
            dPointer2 = { "iToken1": iToken1, "iNode": dNode["<>"], "bKeep": True }
            yield from self._getNextPointers(dToken, dGraph, dPointer2, bDebug)

    def parseGraph (self, dGraph, sCountry="FR", dOptions=None, bShowRuleId=False, bDebug=False, bContext=False):
        "parse graph with tokens from the text and execute actions encountered"
        lPointer = []
        bTagAndRewrite = False
        for iToken, dToken in enumerate(self.lToken):
            if bDebug:
                echo("TOKEN: " + dToken["sValue"])
            # check arcs for each existing pointer
            lNextPointer = []
            for dPointer in lPointer:
                lNextPointer.extend(self._getNextPointers(dToken, dGraph, dPointer, bDebug))
            lPointer = lNextPointer
            # check arcs of first nodes
            lPointer.extend(self._getNextPointers(dToken, dGraph, { "iToken1": iToken, "iNode": 0 }, bDebug))
            # check if there is rules to check for each pointer
            for dPointer in lPointer:
                #if bDebug:
                #    echo("+", dPointer)
                if "<rules>" in dGraph[dPointer["iNode"]]:
                    bChange = self._executeActions(dGraph, dGraph[dPointer["iNode"]]["<rules>"], dPointer["iToken1"]-1, iToken, dOptions, sCountry, bShowRuleId, bDebug, bContext)
                    if bChange:
                        bTagAndRewrite = True
        if bTagAndRewrite:
            self.rewriteFromTags(bDebug)
        if bDebug:
            echo(self)
        return self.sSentence

    def _executeActions (self, dGraph, dNode, nTokenOffset, nLastToken, dOptions, sCountry, bShowRuleId, bDebug, bContext):
        "execute actions found in the DARG"
        bChange = False
        for sLineId, nextNodeKey in dNode.items():
            bCondMemo = None
            for sRuleId in dGraph[nextNodeKey]:
                try:
                    if bDebug:
                        echo("   >TRY: " + sRuleId + " " + sLineId)
                    _, sOption, sFuncCond, cActionType, sWhat, *eAct = _rules_graph.dRule[sRuleId]
                    # Suggestion    [ option, condition, "-", replacement/suggestion/action, iTokenStart, iTokenEnd, cStartLimit, cEndLimit, bCaseSvty, nPriority, sMessage, sURL ]
                    # TextProcessor [ option, condition, "~", replacement/suggestion/action, iTokenStart, iTokenEnd, bCaseSvty ]
                    # Disambiguator [ option, condition, "=", replacement/suggestion/action ]
                    # Tag           [ option, condition, "/", replacement/suggestion/action, iTokenStart, iTokenEnd ]
                    # Immunity      [ option, condition, "!", "",                            iTokenStart, iTokenEnd ]
                    # Test          [ option, condition, ">", "" ]
                    if not sOption or dOptions.get(sOption, False):
                        bCondMemo = not sFuncCond or globals()[sFuncCond](self.lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, self.dTags, self.sSentence, self.sSentence0)
                        if bCondMemo:
                            if cActionType == "-":
                                # grammar error
                                iTokenStart, iTokenEnd, cStartLimit, cEndLimit, bCaseSvty, nPriority, sMessage, sURL = eAct
                                nTokenErrorStart = nTokenOffset + iTokenStart  if iTokenStart > 0  else nLastToken + iTokenStart
                                if "bImmune" not in self.lToken[nTokenErrorStart]:
                                    nTokenErrorEnd = nTokenOffset + iTokenEnd  if iTokenEnd > 0  else nLastToken + iTokenEnd
                                    nErrorStart = self.nOffsetWithinParagraph + (self.lToken[nTokenErrorStart]["nStart"] if cStartLimit == "<"  else self.lToken[nTokenErrorStart]["nEnd"])
                                    nErrorEnd = self.nOffsetWithinParagraph + (self.lToken[nTokenErrorEnd]["nEnd"] if cEndLimit == ">"  else self.lToken[nTokenErrorEnd]["nStart"])
                                    if nErrorStart not in self.dError or nPriority > self.dErrorPriority.get(nErrorStart, -1):
                                        self.dError[nErrorStart] = self._createErrorFromTokens(sWhat, nTokenOffset, nLastToken, nTokenErrorStart, nErrorStart, nErrorEnd, sLineId, sRuleId, bCaseSvty, sMessage, sURL, bShowRuleId, sOption, bContext)
                                        self.dErrorPriority[nErrorStart] = nPriority
                                        self.dSentenceError[nErrorStart] = self.dError[nErrorStart]
                                        if bDebug:
                                            echo("    NEW_ERROR: {}".format(self.dError[nErrorStart]))
                            elif cActionType == "~":
                                # text processor
                                nTokenStart = nTokenOffset + eAct[0]  if eAct[0] > 0  else nLastToken + eAct[0]
                                nTokenEnd = nTokenOffset + eAct[1]  if eAct[1] > 0  else nLastToken + eAct[1]
                                self._tagAndPrepareTokenForRewriting(sWhat, nTokenStart, nTokenEnd, nTokenOffset, nLastToken, eAct[2], bDebug)
                                bChange = True
                                if bDebug:
                                    echo("    TEXT_PROCESSOR: [{}:{}]  > {}".format(self.lToken[nTokenStart]["sValue"], self.lToken[nTokenEnd]["sValue"], sWhat))
                            elif cActionType == "=":
                                # disambiguation
                                globals()[sWhat](self.lToken, nTokenOffset, nLastToken)
                                if bDebug:
                                    echo("    DISAMBIGUATOR: ({})  [{}:{}]".format(sWhat, self.lToken[nTokenOffset+1]["sValue"], self.lToken[nLastToken]["sValue"]))
                            elif cActionType == ">":
                                # we do nothing, this test is just a condition to apply all following actions
                                if bDebug:
                                    echo("    COND_OK")
                            elif cActionType == "/":
                                # Tag
                                nTokenStart = nTokenOffset + eAct[0]  if eAct[0] > 0  else nLastToken + eAct[0]
                                nTokenEnd = nTokenOffset + eAct[1]  if eAct[1] > 0  else nLastToken + eAct[1]
                                for i in range(nTokenStart, nTokenEnd+1):
                                    if "aTags" in self.lToken[i]:
                                        self.lToken[i]["aTags"].update(sWhat.split("|"))
                                    else:
                                        self.lToken[i]["aTags"] = set(sWhat.split("|"))
                                if bDebug:
                                    echo("    TAG: {} >  [{}:{}]".format(sWhat, self.lToken[nTokenStart]["sValue"], self.lToken[nTokenEnd]["sValue"]))
                                for sTag in sWhat.split("|"):
                                    if sTag not in self.dTags:
                                        self.dTags[sTag] = [nTokenStart, nTokenEnd]
                                    else:
                                        self.dTags[sTag][0] = min(nTokenStart, self.dTags[sTag][0])
                                        self.dTags[sTag][1] = max(nTokenEnd, self.dTags[sTag][1])
                            elif cActionType == "!":
                                # immunity
                                if bDebug:
                                    echo("    IMMUNITY: " + sLineId + " / " + sRuleId)
                                nTokenStart = nTokenOffset + eAct[0]  if eAct[0] > 0  else nLastToken + eAct[0]
                                nTokenEnd = nTokenOffset + eAct[1]  if eAct[1] > 0  else nLastToken + eAct[1]
                                if nTokenEnd - nTokenStart == 0:
                                    self.lToken[nTokenStart]["bImmune"] = True
                                    nErrorStart = self.nOffsetWithinParagraph + self.lToken[nTokenStart]["nStart"]
                                    if nErrorStart in self.dError:
                                        del self.dError[nErrorStart]
                                else:
                                    for i in range(nTokenStart, nTokenEnd+1):
                                        self.lToken[i]["bImmune"] = True
                                        nErrorStart = self.nOffsetWithinParagraph + self.lToken[i]["nStart"]
                                        if nErrorStart in self.dError:
                                            del self.dError[nErrorStart]
                            else:
                                echo("# error: unknown action at " + sLineId)
                        elif cActionType == ">":
                            if bDebug:
                                echo("    COND_BREAK")
                            break
                except Exception as e:
                    raise Exception(str(e), sLineId, sRuleId, self.sSentence)
        return bChange

    def _createErrorFromRegex (self, sText, sText0, sRepl, nOffset, m, iGroup, sLineId, sRuleId, bUppercase, sMsg, sURL, bShowRuleId, sOption, bContext):
        nStart = nOffset + m.start(iGroup)
        nEnd = nOffset + m.end(iGroup)
        # suggestions
        if sRepl[0:1] == "=":
            sSugg = globals()[sRepl[1:]](sText, m)
            lSugg = sSugg.split("|")  if sSugg  else []
        elif sRepl == "_":
            lSugg = []
        else:
            lSugg = m.expand(sRepl).split("|")
        if bUppercase and lSugg and m.group(iGroup)[0:1].isupper():
            lSugg = list(map(lambda s: s[0:1].upper()+s[1:], lSugg))
        # Message
        sMessage = globals()[sMsg[1:]](sText, m)  if sMsg[0:1] == "="  else  m.expand(sMsg)
        if bShowRuleId:
            sMessage += "  #" + sLineId + " / " + sRuleId
        #
        if _bWriterError:
            return self._createErrorForWriter(nStart, nEnd - nStart, sRuleId, sOption, sMessage, lSugg, sURL)
        return self._createErrorAsDict(nStart, nEnd, sLineId, sRuleId, sOption, sMessage, lSugg, sURL, bContext)

    def _createErrorFromTokens (self, sSugg, nTokenOffset, nLastToken, iFirstToken, nStart, nEnd, sLineId, sRuleId, bCaseSvty, sMsg, sURL, bShowRuleId, sOption, bContext):
        # suggestions
        if sSugg[0:1] == "=":
            sSugg = globals()[sSugg[1:]](self.lToken, nTokenOffset, nLastToken)
            lSugg = sSugg.split("|")  if sSugg  else []
        elif sSugg == "_":
            lSugg = []
        else:
            lSugg = self._expand(sSugg, nTokenOffset, nLastToken).split("|")
        if bCaseSvty and lSugg and self.lToken[iFirstToken]["sValue"][0:1].isupper():
            lSugg = list(map(lambda s: s[0:1].upper()+s[1:], lSugg))
        # Message
        sMessage = globals()[sMsg[1:]](self.lToken, nTokenOffset, nLastToken)  if sMsg[0:1] == "="  else self._expand(sMsg, nTokenOffset, nLastToken)
        if bShowRuleId:
            sMessage += "  #" + sLineId + " / " + sRuleId
        #
        if _bWriterError:
            return self._createErrorForWriter(nStart, nEnd - nStart, sRuleId, sOption, sMessage, lSugg, sURL)
        return self._createErrorAsDict(nStart, nEnd, sLineId, sRuleId, sOption, sMessage, lSugg, sURL, bContext)

    def _createErrorForWriter (self, nStart, nLen, sRuleId, sOption, sMessage, lSugg, sURL):
        xErr = SingleProofreadingError()    # uno.createUnoStruct( "com.sun.star.linguistic2.SingleProofreadingError" )
        xErr.nErrorStart = nStart
        xErr.nErrorLength = nLen
        xErr.nErrorType = PROOFREADING
        xErr.aRuleIdentifier = sRuleId
        xErr.aShortComment = sMessage   # sMessage.split("|")[0]     # in context menu
        xErr.aFullComment = sMessage    # sMessage.split("|")[-1]    # in dialog
        xErr.aSuggestions = tuple(lSugg)
        # Properties
        lProperties = []
        if _nUnderliningStyle:
            lProperties.append(PropertyValue(Name="LineType", Value=_nUnderliningStyle))
        if _bMulticolor:
            lProperties.append(PropertyValue(Name="LineColor", Value=_dOptionsColors.get(sOption, 33023)))
        if sURL:
            lProperties.append(PropertyValue(Name="FullCommentURL", Value=sURL))
        xErr.aProperties = lProperties
        return xErr

    def _createErrorAsDict (self, nStart, nEnd, sLineId, sRuleId, sOption, sMessage, lSugg, sURL, bContext):
        dErr = {
            "nStart": nStart,
            "nEnd": nEnd,
            "sLineId": sLineId,
            "sRuleId": sRuleId,
            "sType": sOption  if sOption  else "notype",
            "aColor": _dOptionsColors.get(sOption, None),
            "sMessage": sMessage,
            "aSuggestions": lSugg,
            "URL": sURL
        }
        if bContext:
            dErr['sUnderlined'] = self.sText0[nStart:nEnd]
            dErr['sBefore'] = self.sText0[max(0,nStart-80):nStart]
            dErr['sAfter'] = self.sText0[nEnd:nEnd+80]
        return dErr

    def _expand (self, sText, nTokenOffset, nLastToken):
        for m in re.finditer(r"\\(-?[0-9]+)", sText):
            if m.group(1)[0:1] == "-":
                sText = sText.replace(m.group(0), self.lToken[nLastToken+int(m.group(1))+1]["sValue"])
            else:
                sText = sText.replace(m.group(0), self.lToken[nTokenOffset+int(m.group(1))]["sValue"])
        return sText

    def rewriteText (self, sText, sRepl, iGroup, m, bUppercase):
        "text processor: write <sRepl> in <sText> at <iGroup> position"
        nLen = m.end(iGroup) - m.start(iGroup)
        if sRepl == "*":
            sNew = " " * nLen
        elif sRepl == "_":
            sNew = "_" * nLen
        elif sRepl == "@":
            sNew = "@" * nLen
        elif sRepl[0:1] == "=":
            sNew = globals()[sRepl[1:]](sText, m)
            sNew = sNew + " " * (nLen-len(sNew))
            if bUppercase and m.group(iGroup)[0:1].isupper():
                sNew = sNew.capitalize()
        else:
            sNew = m.expand(sRepl)
            sNew = sNew + " " * (nLen-len(sNew))
        return sText[0:m.start(iGroup)] + sNew + sText[m.end(iGroup):]

    def _tagAndPrepareTokenForRewriting (self, sWhat, nTokenRewriteStart, nTokenRewriteEnd, nTokenOffset, nLastToken, bCaseSvty, bDebug):
        "text processor: rewrite tokens between <nTokenRewriteStart> and <nTokenRewriteEnd> position"
        if sWhat == "*":
            # purge text
            if nTokenRewriteEnd - nTokenRewriteStart == 0:
                self.lToken[nTokenRewriteStart]["bToRemove"] = True
            else:
                for i in range(nTokenRewriteStart, nTokenRewriteEnd+1):
                    self.lToken[i]["bToRemove"] = True
        elif sWhat == "␣":
            # merge tokens
            self.lToken[nTokenRewriteStart]["nMergeUntil"] = nTokenRewriteEnd
        elif sWhat == "_":
            # neutralized token
            if nTokenRewriteEnd - nTokenRewriteStart == 0:
                self.lToken[nTokenRewriteStart]["sNewValue"] = "_"
            else:
                for i in range(nTokenRewriteStart, nTokenRewriteEnd+1):
                    self.lToken[i]["sNewValue"] = "_"
        else:
            if sWhat.startswith("="):
                sWhat = globals()[sWhat[1:]](self.lToken, nTokenOffset, nLastToken)
            else:
                sWhat = self._expand(sWhat, nTokenOffset, nLastToken)
            bUppercase = bCaseSvty and self.lToken[nTokenRewriteStart]["sValue"][0:1].isupper()
            if nTokenRewriteEnd - nTokenRewriteStart == 0:
                # one token
                if bUppercase:
                    sWhat = sWhat[0:1].upper() + sWhat[1:]
                self.lToken[nTokenRewriteStart]["sNewValue"] = sWhat
            else:
                # several tokens
                lTokenValue = sWhat.split("|")
                if len(lTokenValue) != (nTokenRewriteEnd - nTokenRewriteStart + 1):
                    if (bDebug):
                        echo("Error. Text processor: number of replacements != number of tokens.")
                    return
                for i, sValue in zip(range(nTokenRewriteStart, nTokenRewriteEnd+1), lTokenValue):
                    if not sValue or sValue == "*":
                        self.lToken[i]["bToRemove"] = True
                    else:
                        if bUppercase:
                            sValue = sValue[0:1].upper() + sValue[1:]
                        self.lToken[i]["sNewValue"] = sValue

    def rewriteFromTags (self, bDebug=False):
        "rewrite the sentence, modify tokens, purge the token list"
        if bDebug:
            echo("REWRITE")
        lNewToken = []
        nMergeUntil = 0
        dTokenMerger = {}
        for iToken, dToken in enumerate(self.lToken):
            bKeepToken = True
            if dToken["sType"] != "INFO":
                if nMergeUntil and iToken <= nMergeUntil:
                    dTokenMerger["sValue"] += " " * (dToken["nStart"] - dTokenMerger["nEnd"]) + dToken["sValue"]
                    dTokenMerger["nEnd"] = dToken["nEnd"]
                    if bDebug:
                        echo("  MERGED TOKEN: " + dTokenMerger["sValue"])
                    bKeepToken = False
                if "nMergeUntil" in dToken:
                    if iToken > nMergeUntil: # this token is not already merged with a previous token
                        dTokenMerger = dToken
                    if dToken["nMergeUntil"] > nMergeUntil:
                        nMergeUntil = dToken["nMergeUntil"]
                    del dToken["nMergeUntil"]
                elif "bToRemove" in dToken:
                    if bDebug:
                        echo("  REMOVED: " + dToken["sValue"])
                    self.sSentence = self.sSentence[:dToken["nStart"]] + " " * (dToken["nEnd"] - dToken["nStart"]) + self.sSentence[dToken["nEnd"]:]
                    bKeepToken = False
            #
            if bKeepToken:
                lNewToken.append(dToken)
                if "sNewValue" in dToken:
                    # rewrite token and sentence
                    if bDebug:
                        echo(dToken["sValue"] + " -> " + dToken["sNewValue"])
                    dToken["sRealValue"] = dToken["sValue"]
                    dToken["sValue"] = dToken["sNewValue"]
                    nDiffLen = len(dToken["sRealValue"]) - len(dToken["sNewValue"])
                    sNewRepl = (dToken["sNewValue"] + " " * nDiffLen)  if nDiffLen >= 0  else dToken["sNewValue"][:len(dToken["sRealValue"])]
                    self.sSentence = self.sSentence[:dToken["nStart"]] + sNewRepl + self.sSentence[dToken["nEnd"]:]
                    del dToken["sNewValue"]
            else:
                try:
                    del self.dTokenPos[dToken["nStart"]]
                except KeyError:
                    echo(self)
                    echo(dToken)
        if bDebug:
            echo("  TEXT REWRITED: " + self.sSentence)
        self.lToken.clear()
        self.lToken = lNewToken


#### common functions

def option (sOpt):
    "return True if option <sOpt> is active"
    return _dOptions.get(sOpt, False)


#### Functions to get text outside pattern scope

# warning: check compile_rules.py to understand how it works

_zNextWord = re.compile(r" +(\w[\w-]*)")
_zPrevWord = re.compile(r"(\w[\w-]*) +$")

def nextword (s, iStart, n):
    "get the nth word of the input string or empty string"
    m = re.match("(?: +[\\w%-]+){" + str(n-1) + "} +([\\w%-]+)", s[iStart:])
    if not m:
        return None
    return (iStart+m.start(1), m.group(1))


def prevword (s, iEnd, n):
    "get the (-)nth word of the input string or empty string"
    m = re.search("([\\w%-]+) +(?:[\\w%-]+ +){" + str(n-1) + "}$", s[:iEnd])
    if not m:
        return None
    return (m.start(1), m.group(1))


def nextword1 (s, iStart):
    "get next word (optimization)"
    m = _zNextWord.match(s[iStart:])
    if not m:
        return None
    return (iStart+m.start(1), m.group(1))


def prevword1 (s, iEnd):
    "get previous word (optimization)"
    m = _zPrevWord.search(s[:iEnd])
    if not m:
        return None
    return (m.start(1), m.group(1))


def look (s, sPattern, sNegPattern=None):
    "seek sPattern in s (before/after/fulltext), if sNegPattern not in s"
    if sNegPattern and re.search(sNegPattern, s):
        return False
    if re.search(sPattern, s):
        return True
    return False


def look_chk1 (dTokenPos, s, nOffset, sPattern, sPatternGroup1, sNegPatternGroup1=""):
    "returns True if s has pattern sPattern and m.group(1) has pattern sPatternGroup1"
    m = re.search(sPattern, s)
    if not m:
        return False
    try:
        sWord = m.group(1)
        nPos = m.start(1) + nOffset
    except IndexError:
        return False
    return morph(dTokenPos, (nPos, sWord), sPatternGroup1, sNegPatternGroup1)



#### Analyse groups for regex rules

def displayInfo (dTokenPos, tWord):
    "for debugging: retrieve info of word"
    if not tWord:
        echo("> nothing to find")
        return True
    lMorph = _oSpellChecker.getMorph(tWord[1])
    if not lMorph:
        echo("> not in dictionary")
        return True
    echo("TOKENS:", dTokenPos)
    if tWord[0] in dTokenPos and "lMorph" in dTokenPos[tWord[0]]:
        echo("DA: " + str(dTokenPos[tWord[0]]["lMorph"]))
    echo("FSA: " + str(lMorph))
    return True


def morph (dTokenPos, tWord, sPattern, sNegPattern="", bNoWord=False):
    "analyse a tuple (position, word), returns True if not sNegPattern in word morphologies and sPattern in word morphologies (disambiguation on)"
    if not tWord:
        return bNoWord
    lMorph = dTokenPos[tWord[0]]["lMorph"]  if tWord[0] in dTokenPos and "lMorph" in dTokenPos[tWord[0]]  else _oSpellChecker.getMorph(tWord[1])
    if not lMorph:
        return False
    # check negative condition
    if sNegPattern:
        if sNegPattern == "*":
            # all morph must match sPattern
            zPattern = re.compile(sPattern)
            return all(zPattern.search(sMorph)  for sMorph in lMorph)
        zNegPattern = re.compile(sNegPattern)
        if any(zNegPattern.search(sMorph)  for sMorph in lMorph):
            return False
    # search sPattern
    zPattern = re.compile(sPattern)
    return any(zPattern.search(sMorph)  for sMorph in lMorph)


def analyse (sWord, sPattern, sNegPattern=""):
    "analyse a word, returns True if not sNegPattern in word morphologies and sPattern in word morphologies (disambiguation off)"
    lMorph = _oSpellChecker.getMorph(sWord)
    if not lMorph:
        return False
    # check negative condition
    if sNegPattern:
        if sNegPattern == "*":
            zPattern = re.compile(sPattern)
            return all(zPattern.search(sMorph)  for sMorph in lMorph)
        zNegPattern = re.compile(sNegPattern)
        if any(zNegPattern.search(sMorph)  for sMorph in lMorph):
            return False
    # search sPattern
    zPattern = re.compile(sPattern)
    return any(zPattern.search(sMorph)  for sMorph in lMorph)


#### Analyse tokens for graph rules

def g_value (dToken, sValues, nLeft=None, nRight=None):
    "test if <dToken['sValue']> is in sValues (each value should be separated with |)"
    sValue = "|"+dToken["sValue"]+"|"  if nLeft is None  else "|"+dToken["sValue"][slice(nLeft, nRight)]+"|"
    if sValue in sValues:
        return True
    if dToken["sValue"][0:2].istitle(): # we test only 2 first chars, to make valid words such as "Laissez-les", "Passe-partout".
        if sValue.lower() in sValues:
            return True
    elif dToken["sValue"].isupper():
        #if sValue.lower() in sValues:
        #    return True
        sValue = "|"+sValue[1:].capitalize()
        if sValue in sValues:
            return True
        sValue = sValue.lower()
        if sValue in sValues:
            return True
    return False


def g_morph (dToken, sPattern, sNegPattern="", nLeft=None, nRight=None, bMemorizeMorph=True):
    "analyse a token, return True if <sNegPattern> not in morphologies and <sPattern> in morphologies"
    if "lMorph" in dToken:
        lMorph = dToken["lMorph"]
    else:
        if nLeft is not None:
            lMorph = _oSpellChecker.getMorph(dToken["sValue"][slice(nLeft, nRight)])
            if bMemorizeMorph:
                dToken["lMorph"] = lMorph
        else:
            lMorph = _oSpellChecker.getMorph(dToken["sValue"])
    if not lMorph:
        return False
    # check negative condition
    if sNegPattern:
        if sNegPattern == "*":
            # all morph must match sPattern
            zPattern = re.compile(sPattern)
            return all(zPattern.search(sMorph)  for sMorph in lMorph)
        zNegPattern = re.compile(sNegPattern)
        if any(zNegPattern.search(sMorph)  for sMorph in lMorph):
            return False
    # search sPattern
    zPattern = re.compile(sPattern)
    return any(zPattern.search(sMorph)  for sMorph in lMorph)


def g_analyse (dToken, sPattern, sNegPattern="", nLeft=None, nRight=None, bMemorizeMorph=True):
    "analyse a token, return True if <sNegPattern> not in morphologies and <sPattern> in morphologies (disambiguation off)"
    if nLeft is not None:
        lMorph = _oSpellChecker.getMorph(dToken["sValue"][slice(nLeft, nRight)])
        if bMemorizeMorph:
            dToken["lMorph"] = lMorph
    else:
        lMorph = _oSpellChecker.getMorph(dToken["sValue"])
    if not lMorph:
        return False
    # check negative condition
    if sNegPattern:
        if sNegPattern == "*":
            # all morph must match sPattern
            zPattern = re.compile(sPattern)
            return all(zPattern.search(sMorph)  for sMorph in lMorph)
        zNegPattern = re.compile(sNegPattern)
        if any(zNegPattern.search(sMorph)  for sMorph in lMorph):
            return False
    # search sPattern
    zPattern = re.compile(sPattern)
    return any(zPattern.search(sMorph)  for sMorph in lMorph)


def g_merged_analyse (dToken1, dToken2, cMerger, sPattern, sNegPattern="", bSetMorph=True):
    "merge two token values, return True if <sNegPattern> not in morphologies and <sPattern> in morphologies (disambiguation off)"
    lMorph = _oSpellChecker.getMorph(dToken1["sValue"] + cMerger + dToken2["sValue"])
    if not lMorph:
        return False
    # check negative condition
    if sNegPattern:
        if sNegPattern == "*":
            # all morph must match sPattern
            zPattern = re.compile(sPattern)
            bResult = all(zPattern.search(sMorph)  for sMorph in lMorph)
            if bResult and bSetMorph:
                dToken1["lMorph"] = lMorph
            return bResult
        zNegPattern = re.compile(sNegPattern)
        if any(zNegPattern.search(sMorph)  for sMorph in lMorph):
            return False
    # search sPattern
    zPattern = re.compile(sPattern)
    bResult = any(zPattern.search(sMorph)  for sMorph in lMorph)
    if bResult and bSetMorph:
        dToken1["lMorph"] = lMorph
    return bResult


def g_tag_before (dToken, dTags, sTag):
    "returns True if <sTag> is present on tokens before <dToken>"
    if sTag not in dTags:
        return False
    if dToken["i"] > dTags[sTag][0]:
        return True
    return False


def g_tag_after (dToken, dTags, sTag):
    "returns True if <sTag> is present on tokens after <dToken>"
    if sTag not in dTags:
        return False
    if dToken["i"] < dTags[sTag][1]:
        return True
    return False


def g_tag (dToken, sTag):
    "returns True if <sTag> is present on token <dToken>"
    return "aTags" in dToken and sTag in dToken["aTags"]


def g_meta (dToken, sType):
    "returns True if <sType> is equal to the token type"
    return dToken["sType"] == sType


def g_space_between_tokens (dToken1, dToken2, nMin, nMax=None):
    "checks if spaces between tokens is >= <nMin> and <= <nMax>"
    nSpace = dToken2["nStart"] - dToken1["nEnd"]
    if nSpace < nMin:
        return False
    if nMax is not None and nSpace > nMax:
        return False
    return True


def g_token (lToken, i):
    "return token at index <i> in lToken (or the closest one)"
    if i < 0:
        return lToken[0]
    if i >= len(lToken):
        return lToken[-1]
    return lToken[i]



#### Disambiguator for regex rules

def select (dTokenPos, nPos, sWord, sPattern, lDefault=None):
    "Disambiguation: select morphologies of <sWord> matching <sPattern>"
    if not sWord:
        return True
    if nPos not in dTokenPos:
        echo("Error. There should be a token at this position: ", nPos)
        return True
    lMorph = _oSpellChecker.getMorph(sWord)
    if not lMorph or len(lMorph) == 1:
        return True
    lSelect = [ sMorph  for sMorph in lMorph  if re.search(sPattern, sMorph) ]
    if lSelect:
        if len(lSelect) != len(lMorph):
            dTokenPos[nPos]["lMorph"] = lSelect
    elif lDefault:
        dTokenPos[nPos]["lMorph"] = lDefault
    return True


def exclude (dTokenPos, nPos, sWord, sPattern, lDefault=None):
    "Disambiguation: exclude morphologies of <sWord> matching <sPattern>"
    if not sWord:
        return True
    if nPos not in dTokenPos:
        echo("Error. There should be a token at this position: ", nPos)
        return True
    lMorph = _oSpellChecker.getMorph(sWord)
    if not lMorph or len(lMorph) == 1:
        return True
    lSelect = [ sMorph  for sMorph in lMorph  if not re.search(sPattern, sMorph) ]
    if lSelect:
        if len(lSelect) != len(lMorph):
            dTokenPos[nPos]["lMorph"] = lSelect
    elif lDefault:
        dTokenPos[nPos]["lMorph"] = lDefault
    return True


def define (dTokenPos, nPos, lMorph):
    "Disambiguation: set morphologies of token at <nPos> with <lMorph>"
    if nPos not in dTokenPos:
        echo("Error. There should be a token at this position: ", nPos)
        return True
    dTokenPos[nPos]["lMorph"] = lMorph
    return True


#### Disambiguation for graph rules

def g_select (dToken, sPattern, lDefault=None):
    "Disambiguation: select morphologies for <dToken> according to <sPattern>, always return True"
    lMorph = dToken["lMorph"]  if "lMorph" in dToken  else _oSpellChecker.getMorph(dToken["sValue"])
    if not lMorph or len(lMorph) == 1:
        if lDefault:
            dToken["lMorph"] = lDefault
            #echo("DA:", dToken["sValue"], dToken["lMorph"])
        return True
    lSelect = [ sMorph  for sMorph in lMorph  if re.search(sPattern, sMorph) ]
    if lSelect:
        if len(lSelect) != len(lMorph):
            dToken["lMorph"] = lSelect
    elif lDefault:
        dToken["lMorph"] = lDefault
    #echo("DA:", dToken["sValue"], dToken["lMorph"])
    return True


def g_exclude (dToken, sPattern, lDefault=None):
    "Disambiguation: select morphologies for <dToken> according to <sPattern>, always return True"
    lMorph = dToken["lMorph"]  if "lMorph" in dToken  else _oSpellChecker.getMorph(dToken["sValue"])
    if not lMorph or len(lMorph) == 1:
        if lDefault:
            dToken["lMorph"] = lDefault
            #echo("DA:", dToken["sValue"], dToken["lMorph"])
        return True
    lSelect = [ sMorph  for sMorph in lMorph  if not re.search(sPattern, sMorph) ]
    if lSelect:
        if len(lSelect) != len(lMorph):
            dToken["lMorph"] = lSelect
    elif lDefault:
        dToken["lMorph"] = lDefault
    #echo("DA:", dToken["sValue"], dToken["lMorph"])
    return True


def g_add_morph (dToken, lNewMorph):
    "Disambiguation: add a morphology to a token"
    lMorph = dToken["lMorph"]  if "lMorph" in dToken  else _oSpellChecker.getMorph(dToken["sValue"])
    lMorph.extend(lNewMorph)
    dToken["lMorph"] = lMorph
    return True


def g_define (dToken, lMorph):
    "Disambiguation: set morphologies of <dToken>, always return True"
    dToken["lMorph"] = lMorph
    #echo("DA:", dToken["sValue"], lMorph)
    return True


def g_define_from (dToken, nLeft=None, nRight=None):
    "Disambiguation: set morphologies of <dToken> with slicing its value with <nLeft> and <nRight>"
    if nLeft is not None:
        dToken["lMorph"] = _oSpellChecker.getMorph(dToken["sValue"][slice(nLeft, nRight)])
    else:
        dToken["lMorph"] = _oSpellChecker.getMorph(dToken["sValue"])
    return True


def g_change_meta (dToken, sType):
    "Disambiguation: change type of token"
    dToken["sType"] = sType
    return True



#### GRAMMAR CHECKER PLUGINS



#### GRAMMAR CHECKING ENGINE PLUGIN: Parsing functions for French language

from . import cregex as cr


def g_morphVC (dToken, sPattern, sNegPattern=""):
    "lance la fonction g_morph() sur la première partie d’un verbe composé (ex: vient-il)"
    nEnd = dToken["sValue"].rfind("-")
    if dToken["sValue"].count("-") > 1:
        if "-t-" in dToken["sValue"]:
            nEnd = nEnd - 2
        elif re.search("-l(?:es?|a)-(?:[mt]oi|nous|leur)$|(?:[nv]ous|lui|leur)-en$", dToken["sValue"]):
            nEnd = dToken["sValue"][0:nEnd].rfind("-")
    return g_morph(dToken, sPattern, sNegPattern, 0, nEnd, False)


def rewriteSubject (s1, s2):
    "rewrite complex subject: <s1> a prn/patr/npr (M[12P]) followed by “et” and <s2>"
    if s2 == "lui":
        return "ils"
    if s2 == "moi":
        return "nous"
    if s2 == "toi":
        return "vous"
    if s2 == "nous":
        return "nous"
    if s2 == "vous":
        return "vous"
    if s2 == "eux":
        return "ils"
    if s2 in ("elle", "elles"):
        if cr.mbNprMasNotFem(_oSpellChecker.getMorph(s1)):
            return "ils"
        # si épicène, indéterminable, mais OSEF, le féminin l’emporte
        return "elles"
    return s1 + " et " + s2


def apposition (sWord1, sWord2):
    "returns True if nom + nom (no agreement required)"
    return len(sWord2) < 2 or (cr.mbNomNotAdj(_oSpellChecker.getMorph(sWord2)) and cr.mbPpasNomNotAdj(_oSpellChecker.getMorph(sWord1)))


def isAmbiguousNAV (sWord):
    "words which are nom|adj and verb are ambiguous (except être and avoir)"
    lMorph = _oSpellChecker.getMorph(sWord)
    if not cr.mbNomAdj(lMorph) or sWord == "est":
        return False
    if cr.mbVconj(lMorph) and not cr.mbMG(lMorph):
        return True
    return False


def isAmbiguousAndWrong (sWord1, sWord2, sReqMorphNA, sReqMorphConj):
    "use it if <sWord1> won’t be a verb; <sWord2> is assumed to be True via isAmbiguousNAV"
    lMorph2 = _oSpellChecker.getMorph(sWord2)
    if not lMorph2:
        return False
    if cr.checkConjVerb(lMorph2, sReqMorphConj):
        # verb word2 is ok
        return False
    lMorph1 = _oSpellChecker.getMorph(sWord1)
    if not lMorph1:
        return False
    if cr.checkAgreement(lMorph1, lMorph2) and (cr.mbAdj(lMorph2) or cr.mbAdj(lMorph1)):
        return False
    return True


def isVeryAmbiguousAndWrong (sWord1, sWord2, sReqMorphNA, sReqMorphConj, bLastHopeCond):
    "use it if <sWord1> can be also a verb; <sWord2> is assumed to be True via isAmbiguousNAV"
    lMorph2 = _oSpellChecker.getMorph(sWord2)
    if not lMorph2:
        return False
    if cr.checkConjVerb(lMorph2, sReqMorphConj):
        # verb word2 is ok
        return False
    lMorph1 = _oSpellChecker.getMorph(sWord1)
    if not lMorph1:
        return False
    if cr.checkAgreement(lMorph1, lMorph2) and (cr.mbAdj(lMorph2) or cr.mbAdjNb(lMorph1)):
        return False
    # now, we know there no agreement, and conjugation is also wrong
    if cr.isNomAdj(lMorph1):
        return True
    #if cr.isNomAdjVerb(lMorph1): # considered True
    if bLastHopeCond:
        return True
    return False


def checkAgreement (sWord1, sWord2):
    "check agreement between <sWord1> and <sWord1>"
    lMorph2 = _oSpellChecker.getMorph(sWord2)
    if not lMorph2:
        return True
    lMorph1 = _oSpellChecker.getMorph(sWord1)
    if not lMorph1:
        return True
    return cr.checkAgreement(lMorph1, lMorph2)


_zUnitSpecial = re.compile("[µ/⁰¹²³⁴⁵⁶⁷⁸⁹Ωℓ·]")
_zUnitNumbers = re.compile("[0-9]")

def mbUnit (s):
    "returns True it can be a measurement unit"
    if _zUnitSpecial.search(s):
        return True
    if 1 < len(s) < 16 and s[0:1].islower() and (not s[1:].islower() or _zUnitNumbers.search(s)):
        return True
    return False


#### Exceptions

aREGULARPLURAL = frozenset(["abricot", "amarante", "aubergine", "acajou", "anthracite", "brique", "caca", "café", \
                            "carotte", "cerise", "chataigne", "corail", "citron", "crème", "grave", "groseille", \
                            "jonquille", "marron", "olive", "pervenche", "prune", "sable"])
aSHOULDBEVERB = frozenset(["aller", "manger"])


#### GRAMMAR CHECKING ENGINE PLUGIN

#### Check date validity

import datetime


_lDay = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_dMonth = { "janvier":1, "février":2, "mars":3, "avril":4, "mai":5, "juin":6, "juillet":7, "août":8, "aout":8, "septembre":9, "octobre":10, "novembre":11, "décembre":12 }

# Dans Python, datetime.weekday() envoie le résultat comme si nous étions dans un calendrier grégorien universal.
# https://fr.wikipedia.org/wiki/Passage_du_calendrier_julien_au_calendrier_gr%C3%A9gorien
# Selon Grégoire, le jeudi 4 octobre 1582 est immédiatement suivi par le vendredi 15 octobre.
# En France, la bascule eut lieu le 9 décembre 1582 qui fut suivi par le 20 décembre 1582.
# C’est la date retenue pour la bascule dans Grammalecte, mais le calendrier grégorien fut adopté dans le monde diversement.
# Il fallut des siècles pour qu’il soit adopté par l’Occident et une grande partie du reste du monde.
_dGregorianToJulian = {
    "lundi":    "jeudi",
    "mardi":    "vendredi",
    "mercredi": "samedi",
    "jeudi":    "dimanche",
    "vendredi": "lundi",
    "samedi":   "mardi",
    "dimanche": "mercredi"
}


def checkDate (sDay, sMonth, sYear):
    "return True if the date is valid"
    if not sMonth.isdigit():
        sMonth = _dMonth.get(sMonth.lower(), "13")
    try:
        return datetime.date(int(sYear), int(sMonth), int(sDay))
    except ValueError:
        return False
    except TypeError:
        return True


def checkDay (sWeekday, sDay, sMonth, sYear):
    "return True if sWeekday is valid according to the given date"
    xDate = checkDate(sDay, sMonth, sYear)
    if xDate and _getDay(xDate) != sWeekday.lower():
        return False
    # if the date isn’t valid, any day is valid.
    return True


def getDay (sDay, sMonth, sYear):
    "return the day of the date (in Gregorian calendar after 1582-12-20, in Julian calendar before 1582-12-09)"
    xDate = checkDate(sDay, sMonth, sYear)
    if xDate:
        return _getDay(xDate)
    return ""


def _getDay (xDate):
    "return the day of the date (in Gregorian calendar after 1582-12-20, in Julian calendar before 1582-12-09)"
    if xDate.year > 1582:
        # Calendrier grégorien
        return _lDay[xDate.weekday()]
    if xDate.year < 1582:
        # Calendrier julien
        sGregorianDay = _lDay[xDate.weekday()]
        return _dGregorianToJulian.get(sGregorianDay, "Erreur: jour inconnu")
    # 1582
    if xDate.month < 12  or xDate.day <= 9:
        # Calendrier julien
        sGregorianDay = _lDay[xDate.weekday()]
        return _dGregorianToJulian.get(sGregorianDay, "Erreur: jour inconnu")
    if xDate.day >= 20:
        # Calendrier grégorien
        return _lDay[xDate.weekday()]
    # 10 - 19 décembre 1582: jours inexistants en France.
    return ""


#### GRAMMAR CHECKING ENGINE PLUGIN: Suggestion mechanisms

from . import conj
from . import mfsp
from . import phonet


## Verbs

def splitVerb (sVerb):
    "renvoie le verbe et les pronoms séparément"
    iRight = sVerb.rfind("-")
    sSuffix = sVerb[iRight:]
    sVerb = sVerb[:iRight]
    if sVerb.endswith(("-t", "-le", "-la", "-les")):
        iRight = sVerb.rfind("-")
        sSuffix = sVerb[iRight:] + sSuffix
        sVerb = sVerb[:iRight]
    return sVerb, sSuffix


def suggVerb (sFlex, sWho, funcSugg2=None, bVC=False):
    "change <sFlex> conjugation according to <sWho>"
    if bVC:
        sFlex, sSfx = splitVerb(sFlex)
    aSugg = set()
    for sStem in _oSpellChecker.getLemma(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            # we get the tense
            aTense = set()
            for sMorph in _oSpellChecker.getMorph(sFlex):
                for m in re.finditer(">"+sStem+"/.*?(:(?:Y|I[pqsf]|S[pq]|K|P|Q))", sMorph):
                    # stem must be used in regex to prevent confusion between different verbs (e.g. sauras has 2 stems: savoir and saurer)
                    if m:
                        if m.group(1) == ":Y" or m.group(1) == ":Q":
                            aTense.add(":Ip")
                            aTense.add(":Iq")
                            aTense.add(":Is")
                        elif m.group(1) == ":P":
                            aTense.add(":Ip")
                        else:
                            aTense.add(m.group(1))
            for sTense in aTense:
                if sWho == ":1ś" and not conj._hasConjWithTags(tTags, sTense, ":1ś"):
                    sWho = ":1s"
                if conj._hasConjWithTags(tTags, sTense, sWho):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, sTense, sWho))
    if funcSugg2:
        aSugg2 = funcSugg2(sFlex)
        if aSugg2:
            aSugg.add(aSugg2)
    if aSugg:
        if bVC:
            aSugg = list(map(lambda sSug: sSug + sSfx, aSugg))
        return "|".join(aSugg)
    return ""


def suggVerbPpas (sFlex, sPattern=None):
    "suggest past participles for <sFlex>"
    aSugg = set()
    for sStem in _oSpellChecker.getLemma(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            if not sPattern:
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q2"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q3"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q4"))
                aSugg.discard("")
            elif sPattern == ":m:s":
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sPattern == ":m:p":
                if conj._hasConjWithTags(tTags, ":PQ", ":Q2"):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q2"))
                else:
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sPattern == ":f:s":
                if conj._hasConjWithTags(tTags, ":PQ", ":Q3"):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q3"))
                else:
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sPattern == ":f:p":
                if conj._hasConjWithTags(tTags, ":PQ", ":Q4"):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q4"))
                else:
                    aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
            elif sPattern == ":s":
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q3"))
                aSugg.discard("")
            elif sPattern == ":p":
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q2"))
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q4"))
                aSugg.discard("")
            else:
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":PQ", ":Q1"))
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggVerbTense (sFlex, sTense, sWho):
    "change <sFlex> to a verb according to <sTense> and <sWho>"
    aSugg = set()
    for sStem in _oSpellChecker.getLemma(sFlex):
        if conj.hasConj(sStem, sTense, sWho):
            aSugg.add(conj.getConj(sStem, sTense, sWho))
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggVerbImpe (sFlex, bVC=False):
    "change <sFlex> to a verb at imperative form"
    if bVC:
        sFlex, sSfx = splitVerb(sFlex)
    aSugg = set()
    for sStem in _oSpellChecker.getLemma(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            if conj._hasConjWithTags(tTags, ":E", ":2s"):
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":E", ":2s"))
            if conj._hasConjWithTags(tTags, ":E", ":1p"):
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":E", ":1p"))
            if conj._hasConjWithTags(tTags, ":E", ":2p"):
                aSugg.add(conj._getConjWithTags(sStem, tTags, ":E", ":2p"))
    if aSugg:
        if bVC:
            aSugg = list(map(lambda sSug: sSug + sSfx, aSugg))
        return "|".join(aSugg)
    return ""


def suggVerbInfi (sFlex):
    "returns infinitive forms of <sFlex>"
    return "|".join([ sStem  for sStem in _oSpellChecker.getLemma(sFlex)  if conj.isVerb(sStem) ])


_dQuiEst = { "je": ":1s", "j’": ":1s", "j’en": ":1s", "j’y": ":1s", \
             "tu": ":2s", "il": ":3s", "on": ":3s", "elle": ":3s", "nous": ":1p", "vous": ":2p", "ils": ":3p", "elles": ":3p" }
_lIndicatif = [":Ip", ":Iq", ":Is", ":If"]
_lSubjonctif = [":Sp", ":Sq"]

def suggVerbMode (sFlex, cMode, sSuj):
    "returns other conjugations of <sFlex> acconding to <cMode> and <sSuj>"
    if cMode == ":I":
        lMode = _lIndicatif
    elif cMode == ":S":
        lMode = _lSubjonctif
    elif cMode.startswith((":I", ":S")):
        lMode = [cMode]
    else:
        return ""
    sWho = _dQuiEst.get(sSuj.lower(), None)
    if not sWho:
        if sSuj[0:1].islower(): # pas un pronom, ni un nom propre
            return ""
        sWho = ":3s"
    aSugg = set()
    for sStem in _oSpellChecker.getLemma(sFlex):
        tTags = conj._getTags(sStem)
        if tTags:
            for sTense in lMode:
                if conj._hasConjWithTags(tTags, sTense, sWho):
                    aSugg.add(conj._getConjWithTags(sStem, tTags, sTense, sWho))
    if aSugg:
        return "|".join(aSugg)
    return ""


## Nouns and adjectives

def suggPlur (sFlex, sWordToAgree=None, bSelfSugg=False):
    "returns plural forms assuming sFlex is singular"
    if sWordToAgree:
        lMorph = _oSpellChecker.getMorph(sFlex)
        if not lMorph:
            return ""
        sGender = cr.getGender(lMorph)
        if sGender == ":m":
            return suggMasPlur(sFlex)
        if sGender == ":f":
            return suggFemPlur(sFlex)
    aSugg = set()
    if sFlex.endswith("l"):
        if sFlex.endswith("al") and len(sFlex) > 2 and _oSpellChecker.isValid(sFlex[:-1]+"ux"):
            aSugg.add(sFlex[:-1]+"ux")
        if sFlex.endswith("ail") and len(sFlex) > 3 and _oSpellChecker.isValid(sFlex[:-2]+"ux"):
            aSugg.add(sFlex[:-2]+"ux")
    if sFlex.endswith("L"):
        if sFlex.endswith("AL") and len(sFlex) > 2 and _oSpellChecker.isValid(sFlex[:-1]+"UX"):
            aSugg.add(sFlex[:-1]+"UX")
        if sFlex.endswith("AIL") and len(sFlex) > 3 and _oSpellChecker.isValid(sFlex[:-2]+"UX"):
            aSugg.add(sFlex[:-2]+"UX")
    if _oSpellChecker.isValid(sFlex+"s"):
        aSugg.add(sFlex+"s")
    if _oSpellChecker.isValid(sFlex+"x"):
        aSugg.add(sFlex+"x")
    if mfsp.hasMiscPlural(sFlex):
        aSugg.update(mfsp.getMiscPlural(sFlex))
    if not aSugg and bSelfSugg and sFlex.endswith(("s", "x", "S", "X")):
        aSugg.add(sFlex)
    aSugg.discard("")
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggSing (sFlex, bSelfSugg=True):
    "returns singular forms assuming sFlex is plural"
    aSugg = set()
    if sFlex.endswith("ux"):
        if _oSpellChecker.isValid(sFlex[:-2]+"l"):
            aSugg.add(sFlex[:-2]+"l")
        if _oSpellChecker.isValid(sFlex[:-2]+"il"):
            aSugg.add(sFlex[:-2]+"il")
    if sFlex.endswith("UX"):
        if _oSpellChecker.isValid(sFlex[:-2]+"L"):
            aSugg.add(sFlex[:-2]+"L")
        if _oSpellChecker.isValid(sFlex[:-2]+"IL"):
            aSugg.add(sFlex[:-2]+"IL")
    if sFlex.endswith(("s", "x", "S", "X")) and _oSpellChecker.isValid(sFlex[:-1]):
        aSugg.add(sFlex[:-1])
    if bSelfSugg and not aSugg:
        aSugg.add(sFlex)
    aSugg.discard("")
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggMasSing (sFlex, bSuggSimil=False):
    "returns masculine singular forms"
    aSugg = set()
    for sMorph in _oSpellChecker.getMorph(sFlex):
        if not ":V" in sMorph:
            # not a verb
            if ":m" in sMorph or ":e" in sMorph:
                aSugg.add(suggSing(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isMasForm(sStem):
                    aSugg.add(sStem)
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q1") and conj.hasConj(sVerb, ":PQ", ":Q3"):
                # We also check if the verb has a feminine form.
                # If not, we consider it’s better to not suggest the masculine one, as it can be considered invariable.
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q1"))
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":m:[si]"):
            aSugg.add(e)
    aSugg.discard("")
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggMasPlur (sFlex, bSuggSimil=False):
    "returns masculine plural forms"
    aSugg = set()
    for sMorph in _oSpellChecker.getMorph(sFlex):
        if not ":V" in sMorph:
            # not a verb
            if ":m" in sMorph or ":e" in sMorph:
                aSugg.add(suggPlur(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isMasForm(sStem):
                    aSugg.add(suggPlur(sStem))
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q2"):
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q2"))
            elif conj.hasConj(sVerb, ":PQ", ":Q1"):
                sSugg = conj.getConj(sVerb, ":PQ", ":Q1")
                # it is necessary to filter these flexions, like “succédé” or “agi” that are not masculine plural.
                if sSugg.endswith("s"):
                    aSugg.add(sSugg)
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":m:[pi]"):
            aSugg.add(e)
    aSugg.discard("")
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggFemSing (sFlex, bSuggSimil=False):
    "returns feminine singular forms"
    aSugg = set()
    for sMorph in _oSpellChecker.getMorph(sFlex):
        if not ":V" in sMorph:
            # not a verb
            if ":f" in sMorph or ":e" in sMorph:
                aSugg.add(suggSing(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isMasForm(sStem):
                    aSugg.update(mfsp.getFemForm(sStem, False))
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q3"):
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q3"))
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":f:[si]"):
            aSugg.add(e)
    aSugg.discard("")
    if aSugg:
        return "|".join(aSugg)
    return ""


def suggFemPlur (sFlex, bSuggSimil=False):
    "returns feminine plural forms"
    aSugg = set()
    for sMorph in _oSpellChecker.getMorph(sFlex):
        if not ":V" in sMorph:
            # not a verb
            if ":f" in sMorph or ":e" in sMorph:
                aSugg.add(suggPlur(sFlex))
            else:
                sStem = cr.getLemmaOfMorph(sMorph)
                if mfsp.isMasForm(sStem):
                    aSugg.update(mfsp.getFemForm(sStem, True))
        else:
            # a verb
            sVerb = cr.getLemmaOfMorph(sMorph)
            if conj.hasConj(sVerb, ":PQ", ":Q4"):
                aSugg.add(conj.getConj(sVerb, ":PQ", ":Q4"))
    if bSuggSimil:
        for e in phonet.selectSimil(sFlex, ":f:[pi]"):
            aSugg.add(e)
    aSugg.discard("")
    if aSugg:
        return "|".join(aSugg)
    return ""


def hasFemForm (sFlex):
    "return True if there is a feminine form of <sFlex>"
    for sStem in _oSpellChecker.getLemma(sFlex):
        if mfsp.isMasForm(sStem) or conj.hasConj(sStem, ":PQ", ":Q3"):
            return True
    if phonet.hasSimil(sFlex, ":f"):
        return True
    return False


def hasMasForm (sFlex):
    "return True if there is a masculine form of <sFlex>"
    for sStem in _oSpellChecker.getLemma(sFlex):
        if mfsp.isMasForm(sStem) or conj.hasConj(sStem, ":PQ", ":Q1"):
            # what has a feminine form also has a masculine form
            return True
    if phonet.hasSimil(sFlex, ":m"):
        return True
    return False


def switchGender (sFlex, bPlur=None):
    "return feminine or masculine form(s) of <sFlex>"
    aSugg = set()
    if bPlur is None:
        for sMorph in _oSpellChecker.getMorph(sFlex):
            if ":f" in sMorph:
                if ":s" in sMorph:
                    aSugg.add(suggMasSing(sFlex))
                elif ":p" in sMorph:
                    aSugg.add(suggMasPlur(sFlex))
            elif ":m" in sMorph:
                if ":s" in sMorph:
                    aSugg.add(suggFemSing(sFlex))
                elif ":p" in sMorph:
                    aSugg.add(suggFemPlur(sFlex))
                else:
                    aSugg.add(suggFemSing(sFlex))
                    aSugg.add(suggFemPlur(sFlex))
    elif bPlur:
        for sMorph in _oSpellChecker.getMorph(sFlex):
            if ":f" in sMorph:
                aSugg.add(suggMasPlur(sFlex))
            elif ":m" in sMorph:
                aSugg.add(suggFemPlur(sFlex))
    else:
        for sMorph in _oSpellChecker.getMorph(sFlex):
            if ":f" in sMorph:
                aSugg.add(suggMasSing(sFlex))
            elif ":m" in sMorph:
                aSugg.add(suggFemSing(sFlex))
    if aSugg:
        return "|".join(aSugg)
    return ""


def switchPlural (sFlex):
    "return plural or singular form(s) of <sFlex>"
    aSugg = set()
    for sMorph in _oSpellChecker.getMorph(sFlex):
        if ":s" in sMorph:
            aSugg.add(suggPlur(sFlex))
        elif ":p" in sMorph:
            aSugg.add(suggSing(sFlex))
    if aSugg:
        return "|".join(aSugg)
    return ""


def hasSimil (sWord, sPattern=None):
    "return True if there is words phonetically similar to <sWord> (according to <sPattern> if required)"
    return phonet.hasSimil(sWord, sPattern)


def suggSimil (sWord, sPattern=None, bSubst=False, bVC=False):
    "return list of words phonetically similar to sWord and whom POS is matching sPattern"
    if bVC:
        sWord, sSfx = splitVerb(sWord)
    aSugg = phonet.selectSimil(sWord, sPattern)
    if not aSugg or not bSubst:
        for sMorph in _oSpellChecker.getMorph(sWord):
            aSugg.update(conj.getSimil(sWord, sMorph, bSubst))
            break
    if aSugg:
        if bVC:
            aSugg = list(map(lambda sSug: sSug + sSfx, aSugg))
        return "|".join(aSugg)
    return ""


def suggCeOrCet (sWord):
    "suggest “ce” or “cet” or both according to the first letter of <sWord>"
    if re.match("(?i)[aeéèêiouyâîï]", sWord):
        return "cet"
    if sWord[0:1] in "hH":
        return "ce|cet"
    return "ce"


def suggLesLa (sWord):
    "suggest “les” or “la” according to <sWord>"
    if any( ":p" in sMorph  for sMorph in _oSpellChecker.getMorph(sWord) ):
        return "les|la"
    return "la"


_zBinary = re.compile("^[01]+$")

def formatNumber (sNumber):
    "add spaces or hyphens to big numbers"
    nLen = len(sNumber)
    if nLen < 4:
        return sNumber
    sRes = ""
    if "," not in sNumber:
        # nombre entier
        sRes = _formatNumber(sNumber, 3)
        # binaire
        if _zBinary.search(sNumber):
            sRes += "|" + _formatNumber(sNumber, 4)
        # numéros de téléphone
        if nLen == 10:
            if sNumber.startswith("0"):
                sRes += "|" + _formatNumber(sNumber, 2)                                                                 # téléphone français
                if sNumber[1] == "4" and (sNumber[2]=="7" or sNumber[2]=="8" or sNumber[2]=="9"):
                    sRes += "|" + sNumber[0:4] + " " + sNumber[4:6] + " " + sNumber[6:8] + " " + sNumber[8:]            # mobile belge
                sRes += "|" + sNumber[0:3] + " " + sNumber[3:6] + " " + sNumber[6:8] + " " + sNumber[8:]                # téléphone suisse
            sRes += "|" + sNumber[0:4] + " " + sNumber[4:7] + "-" + sNumber[7:]                                         # téléphone canadien ou américain
        elif nLen == 9 and sNumber.startswith("0"):
            sRes += "|" + sNumber[0:3] + " " + sNumber[3:5] + " " + sNumber[5:7] + " " + sNumber[7:9]                   # fixe belge 1
            sRes += "|" + sNumber[0:2] + " " + sNumber[2:5] + " " + sNumber[5:7] + " " + sNumber[7:9]                   # fixe belge 2
    else:
        # Nombre réel
        sInt, sFloat = sNumber.split(",", 1)
        sRes = _formatNumber(sInt, 3) + "," + sFloat
    return sRes

def _formatNumber (sNumber, nGroup=3):
    sRes = ""
    nEnd = len(sNumber)
    while nEnd > 0:
        nStart = max(nEnd-nGroup, 0)
        sRes = sNumber[nStart:nEnd] + " " + sRes  if sRes  else sNumber[nStart:nEnd]
        nEnd = nEnd - nGroup
    return sRes


def formatNF (s):
    "typography: format NF reference (norme française)"
    try:
        m = re.match("NF[  -]?(C|E|P|Q|S|X|Z|EN(?:[  -]ISO|))[  -]?([0-9]+(?:[/‑-][0-9]+|))", s)
        if not m:
            return ""
        return "NF " + m.group(1).upper().replace(" ", " ").replace("-", " ") + " " + m.group(2).replace("/", "‑").replace("-", "‑")
    except (re.error, IndexError):
        traceback.print_exc()
        return "# erreur #"


def undoLigature (c):
    "typography: split ligature character <c> in several chars"
    if c == "ﬁ":
        return "fi"
    if c == "ﬂ":
        return "fl"
    if c == "ﬀ":
        return "ff"
    if c == "ﬃ":
        return "ffi"
    if c == "ﬄ":
        return "ffl"
    if c == "ﬅ":
        return "ft"
    if c == "ﬆ":
        return "st"
    return "_"




_xNormalizedCharsForInclusiveWriting = str.maketrans({
    '(': '_',  ')': '_',
    '.': '_',  '·': '_',  '•': '_',
    '–': '_',  '—': '_',
    '/': '_'
})


def normalizeInclusiveWriting (sToken):
    "typography: replace word separators used in inclusive writing by underscore (_)"
    return sToken.translate(_xNormalizedCharsForInclusiveWriting)



#### CALLABLES FOR REGEX RULES (generated code)

def _c_esp_avant_après_tiret_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not m.group(1).endswith("-t") and m.group(3) != "t" and not (m.group(2) == " -" and m.group(3).isdigit())
def _c_esp_avant_après_tiret_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return (m.group(3) == "je" and morph(dTokenPos, (m.start(1), m.group(1)), ":1s")) or (m.group(3) == "tu" and morph(dTokenPos, (m.start(1), m.group(1)), ":2s")) or (m.group(3) == "il" and morph(dTokenPos, (m.start(1), m.group(1)), ":3s")) or (m.group(3) == "elle" and morph(dTokenPos, (m.start(1), m.group(1)), ":3s")) or (m.group(3) == "on" and morph(dTokenPos, (m.start(1), m.group(1)), ":3s")) or (m.group(3) == "nous" and morph(dTokenPos, (m.start(1), m.group(1)), ":1p")) or (m.group(3) == "vous" and morph(dTokenPos, (m.start(1), m.group(1)), ":2P")) or (m.group(3) == "ils" and morph(dTokenPos, (m.start(1), m.group(1)), ":3p")) or (m.group(3) == "elles" and morph(dTokenPos, (m.start(1), m.group(1)), ":3p"))
def _c_esp_avant_après_tiret_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _c_typo_parenthèse_fermante_collée_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "\\([rR][eéEÉ]$")
def _p_p_URL2_2 (sSentence, m):
    return m.group(2).capitalize()
def _p_p_sigle1_1 (sSentence, m):
    return m.group(1).replace(".", "")+"."
def _c_p_sigle2_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not re.search("(?i)^(?:i\\.e\\.|s\\.[tv]\\.p\\.|e\\.g\\.|a\\.k\\.a\\.|c\\.q\\.f\\.d\\.|b\\.a\\.|n\\.b\\.)$", m.group(0))
def _c_p_sigle2_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0).__len__() == 4
def _s_p_sigle2_2 (sSentence, m):
    return m.group(0).replace(".", "").upper() + "|" + m.group(0)[0:2] + " " + m.group(0)[2:4]
def _c_p_sigle2_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _s_p_sigle2_3 (sSentence, m):
    return m.group(0).replace(".", "").upper()
def _c_p_sigle2_4 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0) != "b.a."
def _p_p_sigle2_4 (sSentence, m):
    return m.group(0).replace(".", "_")
def _p_p_sigle3_1 (sSentence, m):
    return m.group(0).replace(".", "").replace("-","")
def _c_p_prénom_lettre_point_patronyme_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return morph(dTokenPos, (m.start(1), m.group(1)), ":M[12]") and (morph(dTokenPos, (m.start(3), m.group(3)), ":(?:M[12]|V)") or not _oSpellChecker.isValid(m.group(3)))
def _c_p_prénom_lettre_point_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return morph(dTokenPos, (m.start(1), m.group(1)), ":M[12]") and look(sSentence[m.end():], "^\\W+[a-zéèêîïâ]")
def _p_p_patronyme_composé_avec_le_la_les_1 (sSentence, m):
    return m.group(0).replace(" ", "_")
def _c_p_mot_entre_crochets_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(1).isdigit()
def _c_p_mot_entre_crochets_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and morph(dTokenPos, (m.start(1), m.group(1)), ":G")
def _p_p_mot_entre_crochets_2 (sSentence, m):
    return " " + m.group(1) + " "
def _c_p_mot_entre_crochets_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and m.group(1).isalpha()
def _c_eepi_écriture_épicène_tous_toutes_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi")
def _p_eepi_écriture_épicène_tous_toutes_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_ceux_celles_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi")
def _p_eepi_écriture_épicène_ceux_celles_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_pluriel_eur_divers_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi") and m.group(2) != "se"
def _c_eepi_écriture_épicène_pluriel_eur_divers_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi") and m.group(2) == "se"
def _p_eepi_écriture_épicène_pluriel_eur_divers_3 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_pluriel_eux_euses_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi")
def _p_eepi_écriture_épicène_pluriel_eux_euses_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_pluriel_aux_ales_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi")
def _p_eepi_écriture_épicène_pluriel_aux_ales_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_pluriel_er_ère_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi")
def _p_eepi_écriture_épicène_pluriel_er_ère_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_pluriel_if_ive_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi")
def _p_eepi_écriture_épicène_pluriel_if_ive_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_pluriel_e_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not (m.group(0).endswith(".Les") or m.group(0).endswith(".Tes"))
def _p_eepi_écriture_épicène_pluriel_e_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_pluriel_e_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi") and not m.group(0).endswith("les") and not m.group(0).endswith("LES") and not re.search("(?i)·[ntlf]?e·s$", m.group(0))
def _c_eepi_écriture_épicène_pluriel_e_4 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(1).endswith("s") or m.group(1).endswith("S")
def _c_eepi_écriture_épicène_pluriel_e_5 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _c_eepi_écriture_épicène_singulier_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not (m.group(0).endswith(".Le") or m.group(0).endswith(".Ne") or m.group(0).endswith(".De")) and not ((m.group(0).endswith("-le") or m.group(0).endswith("-Le") or m.group(0).endswith("-LE")) and not (m.group(1).endswith("l") or m.group(1).endswith("L")))
def _p_eepi_écriture_épicène_singulier_2 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_eepi_écriture_épicène_singulier_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("eepi") and (m.group(1) == "un" or m.group(1) == "Un" or m.group(1) == "UN")
def _c_eepi_écriture_épicène_singulier_4 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and option("eepi") and not re.search("(?i)·[ntl]?e$", m.group(2))
def _s_eepi_écriture_épicène_singulier_4 (sSentence, m):
    return m.group(1)+"·"+m.group(2)[1:].rstrip(")")
def _p_typo_écriture_invariable_1 (sSentence, m):
    return normalizeInclusiveWriting(m.group(0))
def _c_typo_écriture_invariable_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("typo") and option("eepi") and not m.group(0).endswith("·s") and not (m.group(0).endswith("/s") and morph(dTokenPos, (m.start(1), m.group(1)), ";S"))
def _c_majuscule_après_point_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not re.search("(?i)^(?:etc|[A-Z]|chap|cf|fig|hab|litt|circ|coll|r[eé]f|étym|suppl|bibl|bibliogr|cit|op|vol|déc|nov|oct|janv|juil|avr|sept)$", m.group(1)) and morph(dTokenPos, (m.start(1), m.group(1)), ":") and morph(dTokenPos, (m.start(2), m.group(2)), ":")
def _s_majuscule_après_point_1 (sSentence, m):
    return m.group(2).capitalize()
def _c_majuscule_début_paragraphe_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return look(sSentence[m.end():], "\\w\\w[.] +\\w+")
def _s_majuscule_début_paragraphe_1 (sSentence, m):
    return m.group(1).capitalize()
def _c_poncfin_règle1_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return look(sSentence[:m.start()], "\\w+(?:\\.|[   ][!?]) +(?:[A-ZÉÈÎ]\\w+|[ÀÔ])")
def _c_virgule_manquante_avant_car_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not morph(dTokenPos, (m.start(1), m.group(1)), ":[DR]")
def _c_virgule_manquante_avant_mais_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not morph(dTokenPos, (m.start(1), m.group(1)), ">(?:[mtscl]es|[nv]os|quels)/")
def _c_virgule_manquante_avant_donc_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not morph(dTokenPos, (m.start(1), m.group(1)), ":[VG]")
def _c_virg_virgule_après_point_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not re.search("^(?:etc|[A-Z]|fig|hab|litt|circ|coll|ref|étym|suppl|bibl|bibliogr|cit|vol|déc|nov|oct|janv|juil|avr|sept|pp?)$", m.group(1))
def _c_typo_espace_manquant_après1_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not m.group(1).isdigit()
def _c_typo_espace_manquant_après3_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return (m.group(1).__len__() > 1 and not m.group(1)[0:1].isdigit() and _oSpellChecker.isValid(m.group(1))) or look(sSentence[m.end():], "^’")
def _c_typo_espace_manquant_après4_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(1)[0:1].isupper() or m.group(1).__len__() > 5 or not m.group(1).isalpha() or (m.group(1).__len__() > 1 and _oSpellChecker.isValid(m.group(1)))
def _s_typo_point_après_titre_1 (sSentence, m):
    return m.group(1)[0:-1]
def _c_typo_point_après_numéro_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(1)[1:3] == "os"
def _c_typo_point_après_numéro_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _c_typo_points_suspension1_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "(?i)etc$")
def _s_typo_points_suspension2_1 (sSentence, m):
    return m.group(0).replace("...", "…").rstrip(".")
def _s_typo_virgules_points_1 (sSentence, m):
    return m.group(0).replace(",", ".").replace("...", "…")
def _s_typo_ponctuation_superflue1_1 (sSentence, m):
    return ",|" + m.group(1)
def _s_typo_ponctuation_superflue2_1 (sSentence, m):
    return ";|" + m.group(1)
def _s_typo_ponctuation_superflue3_1 (sSentence, m):
    return ":|" + m.group(0)[1]
def _c_nbsp_ajout_avant_double_ponctuation_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return sCountry != "CA"
def _s_nbsp_ajout_avant_double_ponctuation_1 (sSentence, m):
    return " "+m.group(0)
def _c_typo_signe_multiplication_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not m.group(0).startswith("0x")
def _c_typo_signe_moins_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "\\w$")
def _s_ligatures_typographiques_1 (sSentence, m):
    return undoLigature(m.group(0))
def _c_typo_apostrophe_incorrecte_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not (m.group(2).__len__() == 1  and  m.group(1).endswith("′ "))
def _s_typo_apostrophe_manquante_prudence1_1 (sSentence, m):
    return m.group(1)[:-1]+"’"
def _c_typo_apostrophe_manquante_prudence2_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not option("mapos") and morph(dTokenPos, (m.start(2), m.group(2)), ":V")
def _s_typo_apostrophe_manquante_prudence2_1 (sSentence, m):
    return m.group(1)[:-1]+"’"
def _c_typo_apostrophe_manquante_audace1_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("mapos") and not look(sSentence[:m.start()], "(?i)(?:lettre|caractère|glyphe|dimension|variable|fonction|point) *$")
def _s_typo_apostrophe_manquante_audace1_1 (sSentence, m):
    return m.group(1)[:-1]+"’"
def _c_typo_guillemets_typographiques_doubles_ouvrants_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "[a-zA-Zéïîùàâäôö]$")
def _c_nf_norme_française_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not re.search("^NF (?:C|E|P|Q|S|X|Z|EN(?: ISO|)) [0-9]+(?:‑[0-9]+|)", m.group(0))
def _s_nf_norme_française_1 (sSentence, m):
    return formatNF(m.group(0))
def _c_typo_cohérence_guillemets_chevrons_ouvrants_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "\\w$")
def _c_typo_cohérence_guillemets_chevrons_ouvrants_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[m.end():], "^\\w")
def _c_typo_cohérence_guillemets_chevrons_fermants_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "\\w$")
def _c_typo_cohérence_guillemets_chevrons_fermants_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[m.end():], "^\\w")
def _c_typo_cohérence_guillemets_doubles_ouvrants_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "\\w$")
def _c_typo_cohérence_guillemets_doubles_fermants_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "\\w$")
def _c_typo_cohérence_guillemets_doubles_fermants_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[m.end():], "^\\w")
def _c_typo_guillemet_simple_ouvrant_non_fermé_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return look(sSentence[:m.start()], " $") or look(sSentence[:m.start()], "^ *$|, *$")
def _c_typo_guillemet_simple_fermant_non_ouvert_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return look(sSentence[m.end():], "^ ") or look(sSentence[m.end():], "^ *$|^,")
def _c_unit_nbsp_avant_unités1_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("num")
def _s_unit_nbsp_avant_unités1_1 (sSentence, m):
    return formatNumber(m.group(2)) + " " + m.group(3)
def _c_unit_nbsp_avant_unités1_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _c_unit_nbsp_avant_unités2_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return morph(dTokenPos, (m.start(3), m.group(3)), ";S", ":[VCR]") or mbUnit(m.group(3)) or not _oSpellChecker.isValid(m.group(3))
def _c_unit_nbsp_avant_unités2_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("num")
def _s_unit_nbsp_avant_unités2_2 (sSentence, m):
    return formatNumber(m.group(2)) + " " + m.group(3)
def _c_unit_nbsp_avant_unités2_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _c_unit_nbsp_avant_unités3_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return (m.group(2).__len__() > 4 and not _oSpellChecker.isValid(m.group(3))) or morph(dTokenPos, (m.start(3), m.group(3)), ";S", ":[VCR]") or mbUnit(m.group(3))
def _c_unit_nbsp_avant_unités3_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("num")
def _s_unit_nbsp_avant_unités3_2 (sSentence, m):
    return formatNumber(m.group(2)) + " " + m.group(3)
def _c_unit_nbsp_avant_unités3_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _c_num_grand_nombre_soudé_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not look(sSentence[:m.start()], "NF[  -]?(C|E|P|Q|X|Z|EN(?:[  -]ISO|)) *$")
def _c_num_grand_nombre_soudé_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0).__len__() > 4
def _s_num_grand_nombre_soudé_2 (sSentence, m):
    return formatNumber(m.group(0))
def _c_num_grand_nombre_soudé_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and ((look(sSentence[m.end():], "^(?:,[0-9]+[⁰¹²³⁴⁵⁶⁷⁸⁹]?|[⁰¹²³⁴⁵⁶⁷⁸⁹])") and not (re.search("^[01]+$", m.group(0)) and look(sSentence[m.end():], "^,[01]+\\b"))) or look(sSentence[m.end():], "^[   ]*(?:[kcmµn]?(?:[slgJKΩ]|m[²³]?|Wh?|Hz|dB)|[%‰€$£¥Åℓhj]|min|°C|℃)(?![\\w’'])"))
def _s_num_grand_nombre_soudé_3 (sSentence, m):
    return formatNumber(m.group(0))
def _c_num_nombre_quatre_chiffres_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return morph(dTokenPos, (m.start(2), m.group(2)), ";S", ":[VCR]") or mbUnit(m.group(2))
def _s_num_nombre_quatre_chiffres_1 (sSentence, m):
    return formatNumber(m.group(1))
def _c_num_grand_nombre_avec_points_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("num")
def _s_num_grand_nombre_avec_points_1 (sSentence, m):
    return m.group(0).replace(".", " ")
def _p_num_grand_nombre_avec_points_2 (sSentence, m):
    return m.group(0).replace(".", "_")
def _c_num_grand_nombre_avec_espaces_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return option("num")
def _s_num_grand_nombre_avec_espaces_1 (sSentence, m):
    return m.group(0).replace(" ", " ")
def _p_num_grand_nombre_avec_espaces_2 (sSentence, m):
    return m.group(0).replace(" ", "_")
def _c_date_nombres_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(2) == m.group(4) and not checkDate(m.group(1), m.group(3), m.group(5)) and not look(sSentence[:m.start()], "(?i)\\b(?:version|article|référence)s? +$")
def _c_redondances_paragraphe_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not morph(dTokenPos, (m.start(1), m.group(1)), ":(?:G|V0)|>(?:t(?:antôt|emps|rès)|loin|souvent|parfois|quelquefois|côte|petit|même)/") and not m.group(1)[0].isupper()
def _c_redondances_paragraphe_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return bCondMemo
def _c_ocr_point_interrogation_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return look(sSentence0[m.end():], "^(?: +[A-ZÉÈÂ(]|…|[.][.]+| *$)")
def _c_ocr_exclamation2_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not morph(dTokenPos, nextword1(sSentence, m.end()), ";S") and not morph(dTokenPos, prevword1(sSentence, m.start()), ":R")
def _c_ocr_nombres_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0) == "II"
def _c_ocr_nombres_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and not m.group(0).isdigit()
def _s_ocr_nombres_2 (sSentence, m):
    return m.group(0).replace("O", "0").replace("I", "1")
def _s_ocr_casse_pronom_vconj_1 (sSentence, m):
    return m.group(1).lower()
def _c_mots_composés_inconnus_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not _oSpellChecker.isValid(m.group(0)) and not re.search("(?i)-(?:je|tu|on|nous|vous|ie?ls?|elles?|ce|là|ci|les?|la|leur|une?s|moi|toi|en|y)$", m.group(0))
def _c_ocr_caractères_rares_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0) != "<" and m.group(0) != ">"
def _c_ocr_le_la_les_regex_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0).endswith("e")
def _c_ocr_le_la_les_regex_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and m.group(0).endswith("a")
def _c_ocr_le_la_les_regex_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and m.group(0).endswith("à")
def _c_ocr_le_la_les_regex_4 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _c_conf_1e_1a_1es_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0).endswith("e") and (morph(dTokenPos, nextword1(sSentence, m.end()), ":(?:N.*:[me]:[si]|V)", ":G") or morph(dTokenPos, prevword1(sSentence, m.start()), ">ne/"))
def _c_conf_1e_1a_1es_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0).endswith("a") and (morph(dTokenPos, nextword1(sSentence, m.end()), ":(?:N.*:[fe]:[si]|V)", ":G") or morph(dTokenPos, prevword1(sSentence, m.start()), ">ne/"))
def _c_conf_1e_1a_1es_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0).endswith("es") and (morph(dTokenPos, nextword1(sSentence, m.end()), ":(?:N.*:[pi]|V)", ":G") or morph(dTokenPos, prevword1(sSentence, m.start()), ">ne/"))
def _c_ocr_il_regex_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(0).endswith("s")
def _c_ocr_il_regex_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo
def _p_p_trait_union_conditionnel1_1 (sSentence, m):
    return m.group(0).replace("‑", "")
def _p_p_trait_union_conditionnel2_1 (sSentence, m):
    return m.group(0).replace("‑", "")
def _c_doublon_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not re.search("(?i)^([nv]ous|faire|en|la|lui|donnant|œuvre|h[éoa]|hou|olé|joli|Bora|couvent|dément|sapiens|très|vroum|[0-9]+)$", m.group(1)) and not (re.search("^(?:est|une?)$", m.group(1)) and look(sSentence[:m.start()], "[’']$")) and not (m.group(1) == "mieux" and look(sSentence[:m.start()], "(?i)qui +$"))
def _c_num_lettre_O_zéro1_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not option("ocr")
def _s_num_lettre_O_zéro1_1 (sSentence, m):
    return m.group(0).replace("O", "0")
def _c_num_lettre_O_zéro2_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not option("ocr")
def _s_num_lettre_O_zéro2_1 (sSentence, m):
    return m.group(0).replace("O", "0")
def _c_d_eepi_écriture_épicène_pluriel_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return morph(dTokenPos, (m.start(1), m.group(1)), ":[NAQ]", ":G")
def _d_d_eepi_écriture_épicène_pluriel_1 (sSentence, m, dTokenPos):
    return define(dTokenPos, m.start(1), [":N:A:Q:e:p"])
def _c_d_eepi_écriture_épicène_singulier_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return morph(dTokenPos, (m.start(1), m.group(1)), ":[NAQ]")
def _d_d_eepi_écriture_épicène_singulier_1 (sSentence, m, dTokenPos):
    return define(dTokenPos, m.start(1), [":N:A:Q:e:s"])
def _c_p_références_aux_notes_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not morph(dTokenPos, (m.start(0), m.group(0)), ":") and morph(dTokenPos, (m.start(1), m.group(1)), ":")
def _c_tu_trait_union_douteux_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return _oSpellChecker.isValid(m.group(1)+"-"+m.group(2)) and analyse(m.group(1)+"-"+m.group(2), ":")
def _c_tu_t_euphonique_incorrect_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return re.search("(?i)^(?:ie?ls|elles|tu)$", m.group(2))
def _c_tu_t_euphonique_incorrect_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not bCondMemo and m.group(1) != "-t-" and m.group(1) != "-T-"
def _c_tu_t_euphonique_incorrect_3 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(1) != "-t-"
def _c_tu_t_euphonique_superflu_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(1) != "-t-"
def _c_redondances_phrase_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not morph(dTokenPos, (m.start(1), m.group(1)), ":(?:G|V0)|>même/")
def _c_redondances_phrase_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return bCondMemo
def _c_mc_mot_composé_1 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return not m.group(1).isdigit() and not m.group(2).isdigit() and not morph(dTokenPos, (m.start(0), m.group(0)), ":") and not morph(dTokenPos, (m.start(2), m.group(2)), ":G") and _oSpellChecker.isValid(m.group(1)+m.group(2))
def _c_mc_mot_composé_2 (sSentence, sSentence0, m, dTokenPos, sCountry, bCondMemo):
    return m.group(2) != "là" and not re.search("(?i)^(?:ex|mi|quasi|semi|non|demi|pro|anti|multi|pseudo|proto|extra)$", m.group(1)) and not m.group(1).isdigit() and not m.group(2).isdigit() and not morph(dTokenPos, (m.start(2), m.group(2)), ":G") and not morph(dTokenPos, (m.start(0), m.group(0)), ":") and not _oSpellChecker.isValid(m.group(1)+m.group(2))



#### CALLABLES FOR GRAPH RULES (generated code)

def _g_cond_g0_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 1) and g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 0, 1)
def _g_cond_g0_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 1)
def _g_cond_g0_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 0, 1)
def _g_cond_g0_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 0) and g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 0, 0)
def _g_cond_g0_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 0)
def _g_cond_g0_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 0, 0)
def _g_cond_g0_7 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":1s")
def _g_da_g0_1 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+2], ":Ov")
def _g_cond_g0_8 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2s|V0)")
def _g_cond_g0_9 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3s")
def _g_cond_g0_10 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3s|R)")
def _g_cond_g0_11 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:1p|R)")
def _g_cond_g0_12 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2p|R)")
def _g_cond_g0_13 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3p")
def _g_cond_g0_14 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3p|R)")
def _g_cond_g0_15 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ne|n’|me|m’|te|t’|se|s’|")
def _g_da_g0_2 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+1], ":D")
def _g_da_g0_3 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+2], ":Os")
def _g_cond_g0_16 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ":1p")
def _g_da_g0_4 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+1], ":Os")
def _g_cond_g0_17 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ":2p")
def _g_da_g0_5 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nLastToken-1+1], ":V")
def _g_da_g0_6 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+3], ":(?:[123][sp]|P|Y)")
def _g_da_g0_7 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+2], ":(?:[123][sp]|P|Y)")
def _g_da_g0_8 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nLastToken-1+1], ":[123][sp]")
def _g_cond_g0_18 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":V0")
def _g_cond_g0_19 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R")
def _g_cond_g0_20 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and g_morph(lToken[nTokenOffset], ":Cs|<start>")
def _g_da_g0_9 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+2], ":[123][sp]")
def _g_da_g0_10 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+2], ":M")
def _g_da_g0_11 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nLastToken-1+1], ":E")
def _g_da_g0_12 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+4], ":N")
def _g_da_g0_13 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+2], ":N")
def _g_da_g0_14 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nLastToken-1+1], ":Q")
def _g_cond_g0_21 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:p|>[a-z]+ième/")
def _g_da_g0_15 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+1], ":R")
def _g_da_g0_16 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+1], ":G")
def _g_cond_g0_22 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|n’|j’|tu|t’|m’|s’|")
def _g_cond_g0_23 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo
def _g_da_g0_17 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":G:R"])
def _g_cond_g0_24 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|je|ne|n’|le|la|l’|les|lui|nous|vous|leur|")
def _g_da_g0_18 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+1], ":V")
def _g_da_g0_19 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+2], ":D")
def _g_da_g0_20 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+2], [":N:m:s"])
def _g_cond_g0_25 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">entre/|:D")
def _g_da_g0_21 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":G"])
def _g_da_g0_22 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+2], ":V")
def _g_da_g0_23 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":N:e:i"])
def _g_da_g0_24 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+2], ":(?:[123][sp]|P)")
def _g_da_g0_25 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+3], ":V")
def _g_cond_g0_26 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+3], "|plus|")
def _g_da_g0_26 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+3], ":[123][sp]")
def _g_da_g0_27 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":LN:m:p"])
def _g_da_g0_28 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":LN:f:p"])
def _g_cond_g0_27 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|l’|quelqu’|quelqu|") and not g_value(lToken[nTokenOffset+2], "|a|fut|fût|est|fait|") and not g_morph(lToken[nTokenOffset+2], ":P")
def _g_da_g0_29 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nLastToken-1+1], ":N")
def _g_cond_g0_28 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|semblant|")
def _g_da_g0_30 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+2], ":D")
def _g_da_g0_31 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+4], ":[NA]")
def _g_da_g0_32 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+4], ":[123][sp]")
def _g_cond_g0_29 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D")
def _g_cond_g0_30 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":A.*:[me]:[si]")
def _g_da_g0_33 (lToken, nTokenOffset, nLastToken):
    return g_add_morph(lToken[nTokenOffset+1], [">nombre/:G:D"])
def _g_cond_g0_31 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo
def _g_da_g0_34 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [">nombre/:G:D"])
def _g_da_g0_35 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+2], ":[123][sp]")
def _g_cond_g0_32 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:m|>(?:être|(?:re|)devenir|rester|demeurer|sembler|para[iî]tre)/")
def _g_cond_g0_33 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ">(?:être|(?:re|)devenir|rester|demeurer|sembler|para[iî]tre)/")
def _g_da_g0_36 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":LV"])
def _g_da_g0_37 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":A:e:i"])
def _g_cond_g0_34 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":R")
def _g_cond_g0_35 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":[NA]")
def _g_da_g0_38 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":Cs"])
def _g_da_g0_39 (lToken, nTokenOffset, nLastToken):
    return g_change_meta(lToken[nTokenOffset+1], "WORD")
def _g_da_g0_40 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":N:m:i"])
def _g_da_g0_41 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":N:f:p"])
def _g_cond_g0_36 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 0) and g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 0)
def _g_cond_g0_37 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 0) and g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 0, 0) and g_morph(lToken[nTokenOffset+1], ":N") and g_morph(lToken[nLastToken-1+1], ":N")
def _g_cond_g0_38 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], " ", ":")
def _g_cond_g0_39 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+1], ":M") and g_morph(lToken[nTokenOffset+2], ":V", ":[GM]")
def _g_da_g0_42 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+2], [":M2"])
def _g_da_g0_43 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":T"])
def _g_cond_g0_40 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D.*:[mp]")
def _g_cond_g0_41 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V")
def _g_cond_g0_42 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V")
def _g_cond_g0_43 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":V")
def _g_da_g0_44 (lToken, nTokenOffset, nLastToken):
    return g_define_from(lToken[nTokenOffset+1], 0, -3)
def _g_cond_g0_44 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ">[iî]le/")
def _g_cond_g0_45 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|un|une|")
def _g_cond_g0_46 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":1[sśŝ]")
def _g_sugg_g0_1 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":1ś", None, True)
def _g_cond_g0_47 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and not g_morphVC(lToken[nTokenOffset+1], ":V")
def _g_sugg_g0_2 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":1[sśŝ]", False, True)
def _g_cond_g0_48 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":[ISK].*:2s")
def _g_sugg_g0_3 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":2s", None, True)
def _g_sugg_g0_4 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":2s", False, True)
def _g_cond_g0_49 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":3p", ":3s")
def _g_sugg_g0_5 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":3s", None, True) + "|" + lToken[nTokenOffset+1]["sValue"]+"s"
def _g_cond_g0_50 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":V", ":3s")
def _g_sugg_g0_6 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":3s", None, True)
def _g_cond_g0_51 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":", ":V|>(?:t|voilà)/")
def _g_sugg_g0_7 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":3s", False, True)
def _g_cond_g0_52 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":", ":V|>t/")
def _g_cond_g0_53 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":3s")
def _g_cond_g0_54 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":(?:3s|V0e.*:3p)")
def _g_cond_g0_55 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":", ":V")
def _g_cond_g0_56 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].endswith("se")
def _g_sugg_g0_8 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-2]+"ce"
def _g_cond_g0_57 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":3p")
def _g_sugg_g0_9 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":3p", None, True)
def _g_sugg_g0_10 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":3p", False, True)
def _g_cond_g0_58 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":(?:1p|E:2[sp])")
def _g_sugg_g0_11 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":1p", None, True)
def _g_cond_g0_59 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":", ":V|>(?:chez|malgré)/")
def _g_sugg_g0_12 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":1p", False, True)
def _g_cond_g0_60 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":2p")
def _g_sugg_g0_13 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":2p", None, True)
def _g_cond_g0_61 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":", ":V|>chez/")
def _g_sugg_g0_14 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":2p", False, True)
def _g_da_g0_45 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nLastToken-1+1], [":VCi1:2p"])
def _g_cond_g0_62 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V", ":E")
def _g_sugg_g0_15 (lToken, nTokenOffset, nLastToken):
    return suggVerbImpe(lToken[nTokenOffset+1]["sValue"], True)
def _g_sugg_g0_16 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":E", False, True)
def _g_cond_g0_63 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":", ":V") and not g_value(lToken[nTokenOffset], "|ce|cet|cette|ces|") and not g_value(lToken[nTokenOffset+1], "|par-la|de-la|jusque-la|celui-la|celle-la|ceux-la|celles-la|")
def _g_sugg_g0_17 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+1]["sValue"], ":E", False, True)+"|"+lToken[nTokenOffset+1]["sValue"][:-3]+" là"
def _g_sugg_g0_18 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-1]
def _g_cond_ocr_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\w") and (g_morph(lToken[nTokenOffset+1], ":G", ":M") or g_morph(lToken[nTokenOffset+1], ":[123][sp]", ":[MNA]|>Est/"))
def _g_sugg_ocr_1 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].lower()
def _g_cond_ocr_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\w") and not lToken[nTokenOffset+2]["sValue"].isupper()
def _g_cond_ocr_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return re.search("^[aâeéèêiîouyh]", lToken[nTokenOffset+2]["sValue"])
def _g_cond_ocr_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\d[   ]+$") and not (lToken[nTokenOffset+1]["sValue"].isupper() and g_value(lToken[nLastToken+1], "|.|<end>|"))
def _g_cond_ocr_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 0) and not lToken[nTokenOffset+1]["sValue"].isupper() or g_value(lToken[nTokenOffset+1], "|à|")
def _g_cond_ocr_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|<start>|—|–|")
def _g_sugg_ocr_2 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("a", "â").replace("A", "Â")
def _g_sugg_ocr_3 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("n", "u")
def _g_cond_ocr_7 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|il|ne|n’|âne|ânesse|")
def _g_cond_ocr_8 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|il|ne|elle|")
def _g_cond_ocr_9 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|je|ne|le|la|les|")
def _g_cond_ocr_10 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:f:[si]")
def _g_cond_ocr_11 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|j’|n’|l’|m’|t’|s’|il|on|elle|ça|cela|ceci|")
def _g_cond_ocr_12 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|et|ou|où|")
def _g_cond_ocr_13 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:p")
def _g_cond_ocr_14 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset], "|grand|") and g_value(g_token(lToken, nTokenOffset+1-2), "|au|"))
def _g_sugg_ocr_4 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("rn", "m").replace("in", "m")
def _g_cond_ocr_15 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:m:[si]")
def _g_cond_ocr_16 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:m:p")
def _g_cond_ocr_17 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:[me]")
def _g_cond_ocr_18 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|au|de|en|par|")
def _g_cond_ocr_19 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":R|<start>|>,") or isNextVerb()
def _g_cond_ocr_20 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "[0-9] +$")
def _g_cond_ocr_21 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tu|")
def _g_sugg_ocr_5 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ess", "ass").replace("ESS", "ASS")
def _g_sugg_ocr_6 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("l", "i").replace("L", "I")
def _g_cond_ocr_22 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|il|elle|on|") and not g_value(g_token(lToken, nTokenOffset+1-2), "|il|elle|on|")
def _g_cond_ocr_23 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nLastToken+1], ":(?:Ov|Y|W)")
def _g_cond_ocr_24 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":(?:O[on]|3s)")
def _g_cond_ocr_25 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":N", "*")
def _g_sugg_ocr_7 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("o", "e")
def _g_sugg_ocr_8 (lToken, nTokenOffset, nLastToken):
    return "l’"+lToken[nTokenOffset+1]["sValue"][2:] + "|L’"+lToken[nTokenOffset+1]["sValue"][2:] + "|j’"+lToken[nTokenOffset+1]["sValue"][2:] + "|J’"+lToken[nTokenOffset+1]["sValue"][2:]
def _g_cond_ocr_26 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\w") and not g_morph(lToken[nTokenOffset+2], ":Y")
def _g_cond_ocr_27 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\w") and g_morph(lToken[nTokenOffset+1], ":", ":M")
def _g_cond_ocr_28 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return _oSpellChecker.isValid(lToken[nTokenOffset+1]["sValue"][1:])
def _g_sugg_ocr_9 (lToken, nTokenOffset, nLastToken):
    return "v"+lToken[nTokenOffset+1]["sValue"][1:] + "|l’"+lToken[nTokenOffset+1]["sValue"][1:]
def _g_cond_ocr_29 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo
def _g_sugg_ocr_10 (lToken, nTokenOffset, nLastToken):
    return "v"+lToken[nTokenOffset+1]["sValue"][1:]
def _g_cond_ocr_30 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\w") and g_morph(lToken[nTokenOffset+1], ":", ":M") and _oSpellChecker.isValid(lToken[nTokenOffset+1]["sValue"][1:])
def _g_sugg_ocr_11 (lToken, nTokenOffset, nLastToken):
    return "l’"+lToken[nTokenOffset+1]["sValue"][1:] + "|p"+lToken[nTokenOffset+1]["sValue"][1:]
def _g_cond_ocr_31 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:[me]:[si]")
def _g_sugg_ocr_12 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("é", "e").replace("É", "E")
def _g_cond_ocr_32 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:V0|N.*:m:[si])")
def _g_cond_ocr_33 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D:[me]:p")
def _g_cond_ocr_34 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D:(?:m:s|e:p)")
def _g_cond_ocr_35 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:homme|ce|quel|être)/")
def _g_sugg_ocr_13 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("â", "a").replace("Â", "A")
def _g_sugg_ocr_14 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ô", "ê").replace("Ô", "Ê")
def _g_sugg_ocr_15 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("è", "ê").replace("È", "Ê")
def _g_sugg_ocr_16 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("é", "ê").replace("É", "Ê").replace("o", "e").replace("O", "E")
def _g_cond_ocr_36 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tu|ne|n’|")
def _g_sugg_ocr_17 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("l", "t").replace("L", "T")+"|"+lToken[nTokenOffset+1]["sValue"].replace("l", "i").replace("L", "I")
def _g_cond_ocr_37 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ne|il|on|elle|je|")
def _g_cond_ocr_38 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ne|il|on|elle|")
def _g_cond_ocr_39 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ne|tu|")
def _g_cond_ocr_40 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:m:s")
def _g_cond_ocr_41 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:f:s")
def _g_cond_ocr_42 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:[me]:p")
def _g_cond_ocr_43 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|sine|")
def _g_cond_ocr_44 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|statu|")
def _g_cond_ocr_45 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_value(lToken[nTokenOffset+1], "|raine|raines|")
def _g_sugg_ocr_18 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ain", "uin").replace("AIN", "UIN")
def _g_cond_ocr_46 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|generis|")
def _g_cond_ocr_47 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|le|ce|mon|ton|son|du|un|")
def _g_cond_ocr_48 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\w")
def _g_cond_ocr_49 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|je|il|elle|on|ne|ça|")
def _g_sugg_ocr_19 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("a", "o").replace("A", "O")
def _g_sugg_ocr_20 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("n", "u").replace("N", "U")
def _g_cond_ocr_50 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:N.*:f:p|V0e.*:3p)|>(?:tu|ne)/")
def _g_cond_ocr_51 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ce|de|du|un|quel|leur|le|")
def _g_sugg_ocr_21 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("l", "t").replace("L", "T")
def _g_cond_g1_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and not re.search("(?i)^(?:onz[ei]|énième|iourte|ouistiti|ouate|one-?step|ouf|Ouagadougou|I(?:I|V|X|er|ᵉʳ|ʳᵉ|è?re))", lToken[nTokenOffset+2]["sValue"]) and not g_morph(lToken[nTokenOffset+2], ":G")
def _g_sugg_g1_1 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][0:1]+"’"
def _g_cond_g1_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1)
def _g_cond_g1_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"] != "SE" and g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V", ":Q")
def _g_cond_g1_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not re.search("(?i)^(?:onz|énième|ouf|énième|ouistiti|one-?step|I(?:I|V|X|er|ᵉʳ))", lToken[nTokenOffset+2]["sValue"]) and g_morph(lToken[nTokenOffset+2], ":[NA].*:[me]")
def _g_cond_g1_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return _sAppContext != "Writer"
def _g_cond_g1_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"] != "1e" and _sAppContext != "Writer"
def _g_sugg_g1_2 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-1]+"ᵉ"
def _g_cond_g1_7 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"] != "1es" and _sAppContext != "Writer"
def _g_sugg_g1_3 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-2]+"ᵉˢ"
def _g_cond_g1_8 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].endswith("s")
def _g_sugg_g1_4 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("mes", "").replace("è", "").replace("e", "").replace("i", "") + "ᵉˢ"
def _g_cond_g1_9 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo
def _g_sugg_g1_5 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("me", "").replace("è", "").replace("e", "").replace("i", "") + "ᵉ"
def _g_cond_g1_10 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return _sAppContext != "Writer" and not option("romain")
def _g_cond_g1_11 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+1], ":G")
def _g_cond_g1_12 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].endswith("s") or lToken[nTokenOffset+1]["sValue"].endswith("S")
def _g_sugg_g1_6 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("1", "₁").replace("2", "₂").replace("3", "₃").replace("4", "₄").replace("5", "₅").replace("6", "₆").replace("7", "₇").replace("8", "₈").replace("9", "₉").replace("0", "₀")
def _g_cond_g1_13 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].isdigit()
def _g_da_g1_1 (lToken, nTokenOffset, nLastToken):
    return g_change_meta(lToken[nTokenOffset+1], "DATE")
def _g_cond_g1_14 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not checkDate(lToken[nTokenOffset+1]["sValue"], lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g1_15 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDay(lToken[nTokenOffset+1]["sValue"], lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+6]["sValue"])
def _g_sugg_g1_7 (lToken, nTokenOffset, nLastToken):
    return getDay(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+6]["sValue"])
def _g_cond_g1_16 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDay(lToken[nTokenOffset+1]["sValue"], lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+5]["sValue"], lToken[nTokenOffset+7]["sValue"])
def _g_sugg_g1_8 (lToken, nTokenOffset, nLastToken):
    return getDay(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+5]["sValue"], lToken[nTokenOffset+7]["sValue"])
def _g_cond_g1_17 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDay(lToken[nTokenOffset+1]["sValue"], lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+6]["sValue"], lToken[nTokenOffset+8]["sValue"])
def _g_sugg_g1_9 (lToken, nTokenOffset, nLastToken):
    return getDay(lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+6]["sValue"], lToken[nTokenOffset+8]["sValue"])
def _g_cond_g1_18 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDay(lToken[nTokenOffset+1]["sValue"], lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g1_10 (lToken, nTokenOffset, nLastToken):
    return getDay(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_cond_g1_19 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDay(lToken[nTokenOffset+1]["sValue"], lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+5]["sValue"])
def _g_sugg_g1_11 (lToken, nTokenOffset, nLastToken):
    return getDay(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+5]["sValue"])
def _g_cond_g1_20 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +av(?:ant|) +J(?:C|ésus-Christ)") and not checkDay(lToken[nTokenOffset+1]["sValue"], lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+5]["sValue"], lToken[nTokenOffset+6]["sValue"])
def _g_sugg_g1_12 (lToken, nTokenOffset, nLastToken):
    return getDay(lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+5]["sValue"], lToken[nTokenOffset+6]["sValue"])
def _g_cond_g1_21 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NB]", ":V0e") and not g_value(lToken[nLastToken+1], "|où|")
def _g_cond_g1_22 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NB]", ":V0e")
def _g_cond_g1_23 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NB]")
def _g_cond_g1_24 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+3], "|aequo|nihilo|cathedra|absurdo|abrupto|")
def _g_cond_g1_25 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|aequo|nihilo|cathedra|absurdo|abrupto|") and not g_value(lToken[nTokenOffset], "|l’|")
def _g_cond_g1_26 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|drive|plug|sit|")
def _g_cond_g1_27 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D")
def _g_cond_g1_28 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":[WA]", ":N", 6)
def _g_sugg_g1_13 (lToken, nTokenOffset, nLastToken):
    return "quasi " + lToken[nTokenOffset+1]["sValue"][6:]
def _g_cond_g1_29 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], "-", ":")
def _g_cond_g1_30 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and (g_morph(lToken[nTokenOffset+2], ":N") or g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], "-", ":"))
def _g_cond_g1_31 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D|<start>|>,") and g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], "-", ":")
def _g_cond_g1_32 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D") and g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], "-", ":")
def _g_cond_g1_33 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not(lToken[nTokenOffset+2]["sValue"] == "forme" and g_value(lToken[nLastToken+1], "|de|d’|")) and g_morph(lToken[nTokenOffset], ":D") and g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], "-", ":")
def _g_da_g1_2 (lToken, nTokenOffset, nLastToken):
    return g_define_from(lToken[nTokenOffset+1], 7)
def _g_cond_g1_34 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ":[GYB]") and g_morph(lToken[nTokenOffset], ":(?:D|V0e)|<start>|>,") and g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], "-", ":N")
def _g_cond_g1_35 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V") and g_merged_analyse(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], "-", ":V")
def _g_cond_g1_36 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":V") and g_merged_analyse(lToken[nTokenOffset+3], lToken[nTokenOffset+3+1], "-", ":V") and not g_morph(lToken[nTokenOffset], ":R")
def _g_cond_g1_37 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:D|V0e)|<start>|>,") and g_merged_analyse(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], "-", ":N")
def _g_cond_g1_38 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower()
def _g_cond_g1_39 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":[WA]")
def _g_cond_g1_40 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|si|s’|")
def _g_cond_g1_41 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":G")
def _g_cond_g1_42 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset], "|par|") and g_value(g_token(lToken, nTokenOffset+1-2), "|un|"))
def _g_cond_g1_43 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset] , ":D")
def _g_cond_g1_44 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":A.*:[me]:[si]")
def _g_cond_g1_45 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D.*:[me]")
def _g_cond_g1_46 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":O[sv]")
def _g_cond_g1_47 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[DR]|<start>|>,")
def _g_cond_g1_48 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not ( g_morph(lToken[nTokenOffset], ":R") and g_value(lToken[nLastToken+1], "|que|qu’|") )
def _g_cond_g1_49 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|de|d’|")
def _g_cond_g1_50 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|guerre|guerres|")
def _g_cond_g1_51 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":Cs|<start>") and g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1)
def _g_cond_g1_52 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|<start>|") and g_morph(lToken[nTokenOffset+2], ":M")
def _g_cond_g1_53 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|quatre|")
def _g_cond_g1_54 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":B")
def _g_sugg_g1_14 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("-", " ")
def _g_sugg_g1_15 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("-", " ")
def _g_cond_g1_55 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|centre|aile|") and not look(sSentence[lToken[nLastToken]["nEnd"]:], "équipe")
def _g_cond_g1_56 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "équipe")
def _g_cond_g1_57 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "[Pp]ar[ -]ci ?,? *$")
def _g_cond_g1_58 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V0", "", 2)
def _g_sugg_g1_16 (lToken, nTokenOffset, nLastToken):
    return "y " + lToken[nTokenOffset+1]["sValue"][2:]
def _g_sugg_g1_17 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace(" ", "-")
def _g_cond_g1_59 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|dès|des|")
def _g_sugg_g1_18 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("’", "-")
def _g_tp_g1_1 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("’", "-")
def _g_cond_g1_60 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nLastToken-2+1], lToken[nLastToken-2+2], 1, 1) and g_morph(lToken[nLastToken-2+1], ":V.*:1p", ":[GW]") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_1p_")
def _g_cond_g1_61 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillons|sachons|")
def _g_cond_g1_62 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillons|sachons|allons|venons|partons|")
def _g_cond_g1_63 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nLastToken-2+1], lToken[nLastToken-2+2], 1, 1) and g_morph(lToken[nLastToken-2+1], ":V.*:2p", ":[GW]") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2p_")
def _g_cond_g1_64 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:2p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillez|sachez|")
def _g_cond_g1_65 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:2p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillez|sachez|allez|venez|partez|")
def _g_cond_g1_66 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":E", "", 0, -4)
def _g_cond_g1_67 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":E", "", 0, -3)
def _g_cond_g1_68 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|appeler|") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_comme_")
def _g_cond_g1_69 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[123][sp]", ">appeler/|:[NA]") and not g_value(lToken[nTokenOffset], "|que|qu’|") and not (g_value(lToken[nTokenOffset], "|ne|n’|") and g_value(g_token(lToken, nTokenOffset+1-2), "|que|qu’|"))
def _g_cond_g1_70 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1)
def _g_sugg_g1_19 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"]+"’"
def _g_cond_g1_71 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+3], "|t’|priori|posteriori|postériori|contrario|capella|fortiori|")
def _g_cond_g1_72 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+4], "|il|ils|elle|elles|iel|iels|on|ont|")
def _g_sugg_g1_20 (lToken, nTokenOffset, nLastToken):
    return "É"+lToken[nTokenOffset+1]["sValue"][1:]
def _g_tp_g1_2 (lToken, nTokenOffset, nLastToken):
    return "É"+lToken[nTokenOffset+1]["sValue"][1:]
def _g_cond_g1_73 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:[me]")
def _g_cond_g1_74 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not lToken[nTokenOffset+2]["sValue"].isupper()
def _g_sugg_g1_21 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA].*:[si]", True)
def _g_cond_g1_75 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not lToken[nTokenOffset+2]["sValue"].isupper() and not g_value(lToken[nTokenOffset], "|tel|telle|")
def _g_sugg_g1_22 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA].*:[pi]", True)
def _g_cond_g1_76 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not lToken[nTokenOffset+2]["sValue"].isupper() and not g_value(lToken[nTokenOffset], "|tels|telles|")
def _g_cond_g1_77 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|l’|")
def _g_cond_g1_78 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+3], "|peu|") or not g_value(lToken[nTokenOffset+2], "|sous|")
def _g_cond_g1_79 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], " en (?:a|aie|aies|ait|eut|eût|aura|aurait|avait)\\b")
def _g_cond_g1_80 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|nuit|")
def _g_sugg_g1_23 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("vrai", "exact")
def _g_cond_g1_81 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":A|>un")
def _g_cond_g1_82 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|de|des|du|d’|")
def _g_sugg_g1_24 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nTokenOffset+3]["sValue"], "", True)
def _g_cond_g1_83 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":D")
def _g_sugg_g1_25 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("a", "on")
def _g_cond_g1_84 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_morph(lToken[nLastToken-1+1], ":[PQ]") and g_morph(lToken[nTokenOffset], ":V0.*:1s"))
def _g_sugg_g1_26 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":1s")
def _g_cond_g1_85 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_value(lToken[nLastToken-1+1], "|est|es|")
def _g_cond_g1_86 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|soussigné|soussignée|") and not g_morph(lToken[nTokenOffset], ":1s")
def _g_sugg_g1_27 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":(?:1s|Ov)", False)
def _g_sugg_g1_28 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":(?:1s|Ov)", False)
def _g_cond_g1_87 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":V0")
def _g_sugg_g1_29 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":2s")
def _g_cond_g1_88 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2s|V0|R)")
def _g_sugg_g1_30 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":(?:2s|Ov)", False)
def _g_cond_g1_89 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_morph(lToken[nTokenOffset+2], ":[PQ]") and g_morph(lToken[nTokenOffset], ":V0.*:3s"))
def _g_sugg_g1_31 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+2]["sValue"], ":3s")
def _g_cond_g1_90 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":3p")
def _g_sugg_g1_32 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":3s")
def _g_cond_g1_91 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":3p")
def _g_cond_g1_92 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3s") and not g_value(lToken[nTokenOffset], "|t’|") and not g_value(lToken[nLastToken-1+1], "|c’|ce|ou|si|")
def _g_sugg_g1_33 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":(?:3s|Ov)", False)
def _g_cond_g1_93 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3s") and not g_value(lToken[nTokenOffset], "|t’|") and not g_value(lToken[nLastToken-1+1], "|c’|ce|")
def _g_sugg_g1_34 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":(?:3s|Ov)", False)
def _g_cond_g1_94 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3s") and not g_value(lToken[nTokenOffset], "|n’|m’|t’|s’|") and not g_value(lToken[nLastToken-1+1], "|c’|ce|si|")
def _g_sugg_g1_35 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":(?:3s|Oo)", False)
def _g_cond_g1_95 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3s") and not g_value(lToken[nTokenOffset], "|n’|m’|t’|s’|") and not g_value(lToken[nLastToken-1+1], "|c’|ce|")
def _g_sugg_g1_36 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":3s", False)
def _g_cond_g1_96 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ">(?:être|devoir|devenir|pouvoir|vouloir|savoir)/:V", ":3s")
def _g_sugg_g1_37 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3s")
def _g_cond_g1_97 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[YP]") or g_morph(lToken[nTokenOffset+3], ":V", ">(?:être|devoir|devenir|pouvoir|vouloir|savoir)/")
def _g_sugg_g1_38 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"][:-1]+"t"
def _g_cond_g1_98 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|je|tu|il|elle|on|nous|vous|ils|elles|iel|iels|")
def _g_sugg_g1_39 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":1p")
def _g_sugg_g1_40 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":1p")
def _g_sugg_g1_41 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":2p")
def _g_sugg_g1_42 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":2p")
def _g_cond_g1_99 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_morph(lToken[nTokenOffset+2], ":[PQ]") and g_morph(lToken[nTokenOffset], ":V0.*:3p"))
def _g_sugg_g1_43 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+2]["sValue"], ":3p")
def _g_cond_g1_100 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":3s")
def _g_sugg_g1_44 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":3p")
def _g_cond_g1_101 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":3s")
def _g_cond_g1_102 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3p") and not g_value(lToken[nTokenOffset], "|t’|")
def _g_sugg_g1_45 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":(?:3p|Ov)", False)
def _g_sugg_g1_46 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":(?:3p|Ov)", False)
def _g_cond_g1_103 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":[12]s")
def _g_cond_g1_104 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nLastToken-1+1], ":1p")
def _g_cond_g1_105 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nLastToken-1+1], ":2p")
def _g_sugg_g1_47 (lToken, nTokenOffset, nLastToken):
    return suggVerbInfi(lToken[nLastToken-1+1]["sValue"])
def _g_sugg_g1_48 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+4]["sValue"], ":(?:[123][sp]|Y)", False)
def _g_sugg_g1_49 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":(?:[123][sp]|Y)", False)
def _g_cond_g1_106 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R")
def _g_sugg_g1_50 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":(?:[123][sp]|Y)", False)
def _g_cond_g1_107 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and g_morph(lToken[nLastToken-1+1], ":1s", ":(?:E|G|W|M|J|3[sp])")
def _g_cond_g1_108 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nLastToken-1+1], dTags, "_1s_") and not g_morph(lToken[nTokenOffset], ":R") and g_morph(lToken[nLastToken-1+1], ":1s", ":(?:E|G|W|M|J|3[sp]|2p|1p)")
def _g_cond_g1_109 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and g_morph(lToken[nTokenOffset+1], ":1s", ":(?:E|G|W|M|J|3[sp]|N|A|Q)") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w"))
def _g_sugg_g1_51 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":3s")
def _g_cond_g1_110 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and g_morph(lToken[nLastToken-1+1], ":2s", ":(?:E|G|W|M|J|3[sp]|1p)")
def _g_cond_g1_111 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nLastToken-1+1], dTags, "_2s_") and g_morph(lToken[nLastToken-1+1], ":2s", ":(?:E|G|W|M|J|3[sp]|1p)")
def _g_cond_g1_112 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nLastToken-1+1], dTags, "_2s_") and not g_morph(lToken[nTokenOffset], ":R") and g_morph(lToken[nLastToken-1+1], ":2s", ":(?:E|G|W|M|J|3[sp]|2p|1p)")
def _g_cond_g1_113 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and g_morph(lToken[nTokenOffset+1], ":2s", ":(?:E|G|W|M|J|3[sp]|N|A|Q|1p)") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w"))
def _g_cond_g1_114 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and g_morph(lToken[nLastToken-1+1], ":[12]s", ":(?:E|G|W|M|J|3[sp]|2p|1p)")
def _g_cond_g1_115 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nLastToken-1+1], dTags, "_1s_") and not g_tag_before(lToken[nLastToken-1+1], dTags, "_2s_") and g_morph(lToken[nLastToken-1+1], ":[12]s", ":(?:E|G|W|M|J|3[sp]|2p|1p)")
def _g_cond_g1_116 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nLastToken-1+1], dTags, "_1s_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and not g_morph(lToken[nTokenOffset], ":R") and g_morph(lToken[nLastToken-1+1], ":[12]s", ":(?:E|G|W|M|J|3[sp]|2p|1p)")
def _g_cond_g1_117 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w")) and not g_morph(lToken[nTokenOffset], ":[DA].*:p")
def _g_cond_g1_118 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and g_morph(lToken[nTokenOffset+1], ":[12]s", ":(?:E|G|W|M|J|3[sp]|2p|1p|V0e|N|A|Q)") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w"))
def _g_cond_g1_119 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_")
def _g_cond_g1_120 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w")) and not g_morph(lToken[nTokenOffset], ":(?:R|D.*:p)")
def _g_cond_g1_121 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_1s_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w"))
def _g_cond_g1_122 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":1p", ":[EGMNAJ]") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_1p_") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w"))
def _g_sugg_g1_52 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+1]["sValue"], ":3p")
def _g_cond_g1_123 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":2p", ":[EGMNAJ]") and not g_tag_before(lToken[nTokenOffset+2], dTags, "_2p_") and not (lToken[nTokenOffset+1]["sValue"].istitle() and look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "\\w"))
def _g_cond_g1_124 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":K:1s", ">(?:aimer|vouloir)/")
def _g_sugg_g1_53 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+4]["sValue"][:-1]
def _g_cond_g1_125 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":K:1s", ">(?:aimer|vouloir)/")
def _g_sugg_g1_54 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+5]["sValue"][:-1]
def _g_cond_g1_126 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+6], ":K:1s", ">(?:aimer|vouloir)/")
def _g_sugg_g1_55 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+6]["sValue"][:-1]
def _g_cond_g1_127 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+7], ":K:1s", ">(?:aimer|vouloir)/")
def _g_sugg_g1_56 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+7]["sValue"][:-1]
def _g_cond_g1_128 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and lToken[nTokenOffset+2]["sValue"].islower()
def _g_cond_g1_129 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"] == "l’"
def _g_cond_g1_130 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and lToken[nTokenOffset+3]["sValue"].islower()
def _g_sugg_g1_57 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:[fe]:[si]", True)
def _g_cond_g1_131 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset], "|le|la|les|") and hasSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:[fe]:[si]")
def _g_cond_g1_132 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], "V.....[pqx]")
def _g_cond_g1_133 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_134 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper()
def _g_sugg_g1_58 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:[me]:[si]", True)
def _g_cond_g1_135 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset], "|le|la|les|")
def _g_cond_g1_136 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset+2], "|sortir|")
def _g_cond_g1_137 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset+2], "|faire|sont|soit|fut|fût|serait|sera|seront|soient|furent|fussent|seraient|peut|pouvait|put|pût|pourrait|pourra|doit|dut|dût|devait|devrait|devra|") and hasSimil(lToken[nTokenOffset+2]["sValue"])
def _g_sugg_g1_59 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:.:[si]", True)
def _g_cond_g1_138 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+3]["sValue"].islower()
def _g_sugg_g1_60 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA]:[me]:[si]", True)
def _g_cond_g1_139 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|dont|l’|d’|sauf|excepté|") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\bun à +$")
def _g_sugg_g1_61 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NAQ]:[me]:[si]", True)
def _g_sugg_g1_62 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:.:[pi]", True)
def _g_sugg_g1_63 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:[me]:[pi]", True)
def _g_cond_g1_140 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset], "|le|la|les|") and hasSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:[fe]:[pi]")
def _g_sugg_g1_64 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]:[fe]:[pi]", True)
def _g_cond_g1_141 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset+2], "|soient|soit|sois|puisse|puisses|puissent|")
def _g_cond_g1_142 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].istitle() and not g_value(lToken[nTokenOffset+2], "|jure|")
def _g_sugg_g1_65 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[NA]", True)
def _g_cond_g1_143 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+3]["sValue"].istitle()
def _g_sugg_g1_66 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA]:.:[si]", True)
def _g_cond_g1_144 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 1) and g_morph(lToken[nTokenOffset+3], ":[NAQ].*:[me]", ":[YG]") and not lToken[nTokenOffset+3]["sValue"].istitle() and not (g_value(lToken[nTokenOffset+3], "|mal|") and g_morph(lToken[nLastToken+1], ":Y"))
def _g_cond_g1_145 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[123][sp]")
def _g_sugg_g1_67 (lToken, nTokenOffset, nLastToken):
    return suggVerbInfi(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g1_146 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[123][sp]", ":[NAQ]") and not lToken[nTokenOffset+3]["sValue"].istitle()
def _g_cond_g1_147 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V1.*:(?:Iq|Ip:2p)", ":1p")
def _g_cond_g1_148 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+3]["sValue"], ":(?:[NA]:[fe]:[si])")
def _g_sugg_g1_68 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":(?:[NA]:[fe]:[si])", True)
def _g_cond_g1_149 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+3]["sValue"].istitle() and not g_value(lToken[nTokenOffset], "|plus|moins|")
def _g_sugg_g1_69 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA]", True)
def _g_cond_g1_150 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nLastToken-1+1]["sValue"].istitle()
def _g_sugg_g1_70 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":[NA]", True)
def _g_cond_g1_151 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+3]["sValue"].istitle() and not g_value(lToken[nTokenOffset], "|plus|moins|un|une|")
def _g_cond_g1_152 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].istitle()
def _g_cond_g1_153 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":V[123].*:[123][sp]|>(?:pouvoir|vouloir|falloir)/")
def _g_sugg_g1_71 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+5]["sValue"])
def _g_cond_g1_154 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":", ":P")
def _g_cond_g1_155 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R") and g_morph(lToken[nTokenOffset+2], ":[NAQ]", ":[PG]")
def _g_cond_g1_156 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":3p")
def _g_sugg_g1_72 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+3]["sValue"], ":PQ", ":P")
def _g_cond_g1_157 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_value(lToken[nTokenOffset+2], "|m’|t’|s’|")
def _g_sugg_g1_73 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"][0:1] + "’en"
def _g_cond_g1_158 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_g1_159 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not g_value(lToken[nTokenOffset+3], "|importe|")
def _g_cond_g1_160 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|n’|")
def _g_cond_g1_161 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":Q") and not g_morph(lToken[nTokenOffset], ":(?:V0a|R)")
def _g_sugg_g1_74 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":m:s")+"|"+suggVerbInfi(lToken[nLastToken-1+1]["sValue"])+"|"+suggVerbTense(lToken[nLastToken-1+1]["sValue"], ":Iq", ":3s")
def _g_sugg_g1_75 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":f:s")+"|"+suggVerbTense(lToken[nLastToken-1+1]["sValue"], ":Iq", ":3s")
def _g_cond_g1_162 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_") and not g_value(lToken[nTokenOffset], "|ou|")
def _g_cond_g1_163 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].istitle() and not g_morph(lToken[nTokenOffset], ":[NA]:[me]:si")
def _g_cond_g1_164 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+3], ">(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)/") and g_morph(lToken[nTokenOffset+2], ":(?:Y|[123][sp])", ":[AQ]")
def _g_sugg_g1_76 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_165 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+3], ">(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)/") and g_morph(lToken[nTokenOffset+2], ":A.*:p", ":[si]")
def _g_sugg_g1_77 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_166 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+3], ">(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)/") and g_morph(lToken[nTokenOffset+2], ":A.*:[fp]", ":[me]:[si]")
def _g_sugg_g1_78 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_167 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+3], ">(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)/") and g_morph(lToken[nTokenOffset+2], ":A.*:[mp]", ":[fe]:[si]")
def _g_sugg_g1_79 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_168 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+3], ">(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)/") and g_morph(lToken[nTokenOffset+2], ":A.*:s", ":[pi]")
def _g_sugg_g1_80 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_169 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+3], ">(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)/") and g_morph(lToken[nTokenOffset+2], ":A.*:[sf]", ":[me]:[pi]")
def _g_sugg_g1_81 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_170 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+3], ">(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)/") and g_morph(lToken[nTokenOffset+2], ":A.*:[sm]", ":[fe]:[pi]")
def _g_sugg_g1_82 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_171 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_")
def _g_cond_g1_172 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|envie|")
def _g_sugg_g1_83 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[AW]", True)
def _g_cond_g1_173 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V1.*:Y", ":[AW]")
def _g_cond_g1_174 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+4]["sValue"] == "soie" or lToken[nTokenOffset+4]["sValue"] == "soies"
def _g_cond_g1_175 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":V", ":3[sp]")
def _g_cond_g1_176 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:p", ":[is]")
def _g_cond_g1_177 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:s", ":[ip]")
def _g_cond_g1_178 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|moins|plus|mieux|")
def _g_cond_g1_179 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not g_value(lToken[nLastToken+1], "|côté|coup|pic|peine|peu|plat|propos|valoir|")
def _g_cond_g1_180 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not g_value(lToken[nLastToken+1], "|côté|coup|pic|peine|peu|plat|propos|valoir|") and not g_morph(lToken[nTokenOffset], ">venir/")
def _g_cond_g1_181 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3s|R)") and not g_morph(lToken[nLastToken+1], ":Oo|>quo?i/")
def _g_cond_g1_182 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D")
def _g_cond_g1_183 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset+2], "|coté|sont|")
def _g_cond_g1_184 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":(?:V.......[_z][az].*:Q|V1.*:Ip:2p)", ":[MGWNY]")
def _g_cond_g1_185 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], "V1.*:(?:Ip:2p|Q)", "*") and not g_value(lToken[nTokenOffset], "|il|elle|on|n’|les|l’|m’|t’|s’|d’|en|y|lui|nous|vous|leur|")
def _g_sugg_g1_84 (lToken, nTokenOffset, nLastToken):
    return suggVerbInfi(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_186 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+2], ":[123][sp]", "*") and not g_value(lToken[nTokenOffset+2], "|tord|tords|")
def _g_cond_g1_187 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V2.*:I[ps]:3s", "*")
def _g_sugg_g1_85 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+2]["sValue"], ":m:s")
def _g_cond_g1_188 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo
def _g_cond_g1_189 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|il|elle|iel|on|n’|m’|t’|l’|") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\bqu[e’] |n’(?:en|y) +$")
def _g_cond_g1_190 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":N", ":Ov")
def _g_cond_g1_191 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:D.*:f:s|A.*:[fe]:[si])|>en/")
def _g_cond_g1_192 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[VN]|<start>", "*")
def _g_cond_g1_193 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":Ov|>(?:il|elle)/")
def _g_cond_g1_194 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset+3], "|sur|") and g_value(lToken[nTokenOffset], "|tout|par|") and g_value(lToken[nTokenOffset+2], "|coup|"))
def _g_cond_g1_195 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:cadeau|offrande|présent)")
def _g_cond_g1_196 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset+1], "|à|") and g_value(lToken[nTokenOffset+2], "|tue-tête|"))
def _g_cond_g1_197 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|l’|n’|il|elle|on|y|") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)n’en +$")
def _g_cond_g1_198 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset+3], "|accès|bon|bonne|beau|besoin|charge|confiance|connaissance|conscience|crainte|droit|envie|été|faim|hâte|honte|interdiction|lieu|mauvaise|peine|peur|raison|rapport|recours|soif|tendance|terre|tort|vent|vocation|") and g_morph(lToken[nTokenOffset+1], ":N", "*")
def _g_cond_g1_199 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ">(?:falloir|aller|pouvoir)/", ">que/")
def _g_cond_g1_200 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ">(?:être|rester|demeurer)/")
def _g_cond_g1_201 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|l’|d’|") and not g_tag(lToken[nTokenOffset], "_en_")
def _g_cond_g1_202 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V", "*") and not g_tag(lToken[nTokenOffset], "_en_")
def _g_cond_g1_203 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|le|du|")
def _g_cond_g1_204 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|les|des|")
def _g_sugg_g1_86 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("scé", "cé").replace("SCÉ", "CÉ")
def _g_sugg_g1_87 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("cé", "scé").replace("CÉ", "SCÉ")
def _g_sugg_g1_88 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("a", "â").replace("A", "Â")
def _g_cond_g1_205 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|,|:D")
def _g_sugg_g1_89 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("é", "ée").replace("É", "ÉE")
def _g_cond_g1_206 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|du|")
def _g_cond_g1_207 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:appeler|considérer|trouver)/")
def _g_cond_g1_208 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset+2], "|ou|") and g_value(lToken[nLastToken+1], "|son|ses|"))
def _g_cond_g1_209 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|oh|ah|") and not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +et là")
def _g_cond_g1_210 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 0, 0) and not (g_value(lToken[nTokenOffset+2], "|a|") and g_value(lToken[nLastToken+1], "|été|"))
def _g_cond_g1_211 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_value(lToken[nLastToken+1], "|été|")
def _g_cond_g1_212 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +en +heure")
def _g_sugg_g1_90 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("o", "a").replace("O", "A")
def _g_cond_g1_213 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+2], ":[NA]")
def _g_cond_g1_214 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and lToken[nTokenOffset+2]["sValue"].islower() and not g_value(lToken[nTokenOffset+2], "|faire|")
def _g_cond_g1_215 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not g_value(lToken[nTokenOffset+2], "|quelques|")
def _g_cond_g1_216 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|que|qu’|")
def _g_cond_g1_217 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"] == "a"
def _g_cond_g1_218 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (lToken[nTokenOffset+3]["sValue"] == "ce" and g_value(lToken[nLastToken+1], "|moment|"))
def _g_sugg_g1_91 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("tt", "t").replace("TT", "T")
def _g_cond_g1_219 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+1], ":Q|>(?:profiter|bénéficier|nombre|tant)/") and not g_morph(lToken[nLastToken+1], ">(?:financi[eè]re?|pécuni(?:er|aire)|sociaux)s?/")
def _g_cond_g1_220 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morphVC(lToken[nTokenOffset+1], ">(?:profiter|bénéficier)/") and not g_morph(lToken[nLastToken+1], ">(?:financière|pécuni(?:er|aire)|sociale)/")
def _g_sugg_g1_92 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("nud", "nu").replace("NUD", "NU")
def _g_cond_g1_221 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:D.*:p|B)|>de/")
def _g_cond_g1_222 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|un|une|les|ces|mes|tes|ses|nos|vos|leurs|quelques|plusieurs|")
def _g_cond_g1_223 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and hasSimil(lToken[nTokenOffset+2]["sValue"], ":[NA].*:[pi]")
def _g_cond_g1_224 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|%|") and not g_morph(lToken[nTokenOffset], ":B|>(?:pourcent|barre|seuil|aucun|plusieurs|certaine?s|une?)/")
def _g_cond_g1_225 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R|>(?:approcher|anniversaire|cap|célébration|commémoration|occasion|passage|programme|terme|classe|délai|échéance|autour|celui|ceux|celle|celles)/") and not g_value(lToken[nLastToken+1], "|de|du|des|d’|") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "% +$")
def _g_cond_g1_226 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R|>(?:approcher|cap|passage|programme|terme|classe|autour|celui|ceux|celle|celles)/") and not g_value(lToken[nLastToken+1], "|de|du|des|d’|") and lToken[nTokenOffset+2]["sValue"] != "35"
def _g_cond_g1_227 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R|>(?:approcher|cap|passage|programme|terme|classe|autour|celui|ceux|celle|celles)/") and not g_value(lToken[nLastToken+1], "|de|du|des|d’|")
def _g_cond_g1_228 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":E")
def _g_sugg_g1_93 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("que", "c").replace("QUE", "C")
def _g_cond_g1_229 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":W")
def _g_sugg_g1_94 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("nd", "nt").replace("ND", "NT")
def _g_sugg_g1_95 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("nd", "nt").replace("ND", "NT")
def _g_cond_g1_230 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":[NA].*:[fe]:[pi]", ":G")
def _g_cond_g1_231 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":[DB]") and g_morph(lToken[nTokenOffset+2], ":N", ":[GAWM]")
def _g_cond_g1_232 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|de|d’|des|du|") and not g_value(g_token(lToken, nLastToken+2), "|de|d’|des|du|")
def _g_cond_g1_233 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":[NA].*:[me]")
def _g_cond_g1_234 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|que|qu’|sûr|davantage|entendu|d’|avant|souvent|longtemps|des|moins|plus|trop|loin|au-delà|") and not g_morph(lToken[nLastToken+1], ":[YAW]")
def _g_cond_g1_235 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset+1], "|emballé|") and g_value(lToken[nLastToken-1+1], "|pesé|")) and g_morph(lToken[nTokenOffset], ":C|<start>|>,")
def _g_cond_g1_236 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V", ":A")
def _g_sugg_g1_96 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("a", "").replace("A", "")
def _g_cond_g1_237 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|il|ils|ne|en|y|leur|lui|nous|vous|me|te|se|la|le|les|qui|<start>|,|")
def _g_sugg_g1_97 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("c", "").replace("C", "")
def _g_sugg_g1_98 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("an", "anc").replace("AN", "ANC")
def _g_sugg_g1_99 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("au", "o").replace("AU", "O")
def _g_cond_g1_238 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:[123][sp]|Y)", "*") and not g_value(lToken[nLastToken+1], "|civile|commerciale|froide|mondiale|nucléaire|préventive|psychologique|sainte|totale|")
def _g_cond_g1_239 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D.*:f:s")
def _g_sugg_g1_100 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("û", "u")
def _g_cond_g1_240 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":[123][sp]", ":[GQ]")
def _g_cond_g1_241 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":[123][sp]", ":[GQ]")
def _g_cond_g1_242 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":[123][sp]", ":[GQ]")
def _g_cond_g1_243 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not lToken[nTokenOffset+2]["sValue"].isupper() and not g_morph(lToken[nTokenOffset], ":E|>le/")
def _g_sugg_g1_101 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"][:-2]+"là"
def _g_sugg_g1_102 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-2]+"là"
def _g_cond_g1_244 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V", ":[NA]", 0, -3)
def _g_cond_g1_245 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V...t")
def _g_sugg_g1_103 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-3]+"-la|" + lToken[nTokenOffset+1]["sValue"][:-3]+" là"
def _g_sugg_g1_104 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-3]+" là"
def _g_cond_g1_246 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D|<start>|,")
def _g_cond_g1_247 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V") and not g_tag(lToken[nTokenOffset], "_en_")
def _g_cond_g1_248 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">[ld]es/")
def _g_cond_g1_249 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C|>,/")
def _g_cond_g1_250 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C|>,/") and g_analyse(lToken[nLastToken-1+1], ":(?:Q|V1.*:Y)", ":N.*:[fe]")
def _g_cond_g1_251 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (lToken[nTokenOffset+1]["sValue"].islower() or g_value(lToken[nTokenOffset], "|<start>|,|")) and lToken[nTokenOffset+2]["sValue"].islower()
def _g_cond_g1_252 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|père|")
def _g_cond_g1_253 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|le|la|les|du|des|au|aux|")
def _g_cond_g1_254 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[me]:s")
def _g_cond_g1_255 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:m:[si]")
def _g_cond_g1_256 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":V.*:3s") and not look(sSentence0[:lToken[1+nTokenOffset]["nStart"]], "’$")
def _g_cond_g1_257 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[VR]|<start>") and not g_morph(lToken[nLastToken+1], ":(?:3s|Ov)")
def _g_cond_g1_258 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|il|ils|elle|elles|iel|iels|")
def _g_sugg_g1_105 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-1]
def _g_cond_g1_259 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and not g_value(lToken[nTokenOffset+2], "|soit|") and g_morph(lToken[nTokenOffset+2], ":3s")
def _g_sugg_g1_106 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("a", "â").replace("A", "Â")
def _g_cond_g1_260 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:[me]|>(?:grande|petite)/")
def _g_cond_g1_261 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-3+1], ":V")
def _g_cond_g1_262 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":V")
def _g_sugg_g1_107 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("o", "au").replace("O", "AU")
def _g_sugg_g1_108 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("pé", "pê").replace("Pé", "Pê").replace("PÉ", "PÊ")
def _g_sugg_g1_109 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("pé", "pê").replace("Pé", "Pê").replace("PÉ", "PÊ")
def _g_cond_g1_263 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:très|en|un|de|du)")
def _g_cond_g1_264 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":C|<start>")
def _g_cond_g1_265 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|quelqu’|l’|d’|sauf|")
def _g_cond_g1_266 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ">seul/") and not g_morph(lToken[nTokenOffset], ">(?:je|tu|il|on|ne)")
def _g_sugg_g1_110 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("n", "nt").replace("N", "NT")
def _g_cond_g1_267 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|la|en|une|") and not g_value(lToken[nLastToken+1], "|position|dance|")
def _g_cond_g1_268 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":Y|<start>")
def _g_sugg_g1_111 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("om", "au").replace("OM", "AU")
def _g_sugg_g1_112 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("au", "om").replace("AU", "OM")
def _g_cond_g1_269 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|peu|de|") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\bau plus $")
def _g_cond_g1_270 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D") and not g_morph(g_token(lToken, nTokenOffset+1-2), ">obtenir/")
def _g_cond_g1_271 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D.*:[pm]")
def _g_cond_g1_272 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D.*:[mp]|<start>")
def _g_cond_g1_273 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:arriver|venir|à|revenir|partir|repartir|aller|de)/") and not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +[mts]on tour[, ]")
def _g_cond_g1_274 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:arriver|venir|à|revenir|partir|repartir|aller|de)/")
def _g_cond_g1_275 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|à|au|aux|")
def _g_cond_g1_276 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ ne s(?:ai[st]|u[ts]|avai(?:s|t|ent)|urent) ")
def _g_cond_g1_277 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset+2], "|en|ne|")  and g_morph(lToken[nLastToken+1], ":V0e"))
def _g_cond_g1_278 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not (g_morph(lToken[nTokenOffset+2], ">(?:pouvoir|devoir|aller)/") and (g_morph(lToken[nLastToken+1], ":V0e") or g_morph(g_token(lToken, nLastToken+2), ":V0e"))) and not (g_morph(lToken[nTokenOffset+2], ":V0a") and g_value(lToken[nLastToken+1], "|été|"))
def _g_cond_g1_279 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset+2], "|en|ne|") and g_morph(lToken[nLastToken+1], ":V0e"))
def _g_cond_g1_280 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[123][sp]")
def _g_sugg_g1_113 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("réso", "raiso")
def _g_sugg_g1_114 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("è", "ai").replace("È", "AI")
def _g_sugg_g1_115 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("ai", "è").replace("AI", "È")
def _g_sugg_g1_116 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ai", "è").replace("AI", "È")
def _g_cond_g1_281 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:R|[123][sp])|<start>")
def _g_sugg_g1_117 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("sen", "cen").replace("Cen", "Sen").replace("CEN", "SEN")
def _g_cond_g1_282 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":(?:[123]s|Q)")
def _g_cond_g1_283 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+3], ":(?:[123]p|Y|P)")
def _g_cond_g1_284 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not g_value(lToken[nTokenOffset], "|ne|il|ils|on|")
def _g_sugg_g1_118 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+2]["sValue"], ":[AWGT]", True)
def _g_cond_g1_285 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+1]["sValue"].isupper() and not g_value(lToken[nTokenOffset], "|ne|il|ils|on|") and not (g_morph(lToken[nTokenOffset+2], ":V0") and g_morph(lToken[nTokenOffset+3], ":[QY]"))
def _g_cond_g1_286 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nLastToken-2+1]["sValue"].islower() and g_morph(lToken[nTokenOffset+2], ":M")
def _g_cond_g1_287 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[si]")
def _g_cond_g1_288 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]")
def _g_cond_g1_289 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]", ":3p")
def _g_cond_g1_290 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], " soit ")
def _g_cond_g1_291 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":[GY]|<end>", ">à/") and not g_value(lToken[nTokenOffset], "|il|on|elle|n’|m’|t’|s’|") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)quel(?:s|les?|) qu[’ ]$") and not look(sSentence[lToken[nLastToken]["nEnd"]:], " soit ")
def _g_cond_g1_292 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[YQ]|>(?:avec|contre|par|pour|sur)/|<start>|>,")
def _g_cond_g1_293 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], "[123][sp]")
def _g_cond_g1_294 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:V|Cs|R)", ":(?:[NA].*:[pi]|Ov)") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_")
def _g_cond_g1_295 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ils|elles|iels|leur|lui|nous|vous|m’|t’|s’|l’|") and not g_tag(lToken[nTokenOffset], "_ceque_")
def _g_cond_g1_296 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:m:s")
def _g_sugg_g1_119 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("u", "û").replace("U", "Û")
def _g_sugg_g1_120 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("u", "û").replace("U", "Û")
def _g_sugg_g1_121 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("au", "ô").replace("AU", "Ô")
def _g_sugg_g1_122 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("è", "ê").replace("È", "Ê")
def _g_sugg_g1_123 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("è", "ê").replace("È", "Ê")
def _g_cond_g1_297 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:D|A.*:m)")
def _g_cond_g1_298 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D|<start>|>,")
def _g_cond_g1_299 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].istitle() and not g_morph(lToken[nTokenOffset], ":O[os]|>(?:[ndmts]e|aller|falloir|pouvoir|savoir|vouloir|préférer|faire|penser|imaginer|souhaiter|désirer|espérer|de|à)/") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\b[ndmts](?:e |’(?:en |y ))(?:pas |jamais |) *$")
def _g_cond_g1_300 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[me]:s", ":[123][sp]")
def _g_cond_g1_301 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|j’|n’|il|elle|on|")
def _g_cond_g1_302 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|avenu|")
def _g_cond_g1_303 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|avenue|")
def _g_cond_g1_304 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|avenus|")
def _g_cond_g1_305 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|avenues|")
def _g_cond_g1_306 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].lower() != lToken[nLastToken-1+1]["sValue"].lower()
def _g_cond_g1_307 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].lower() != lToken[nLastToken-2+1]["sValue"].lower()
def _g_cond_g1_308 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].isupper() and not g_value(lToken[nLastToken+1], "|saint|")
def _g_sugg_g1_124 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].lower()
def _g_cond_g1_309 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].isupper() and not g_value(lToken[nLastToken+1], "|gras|saint|")
def _g_cond_g1_310 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+1], ":M1") and not lToken[nTokenOffset+2]["sValue"].isupper()
def _g_cond_g1_311 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].isupper()
def _g_cond_g1_312 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"] == "assemblée"
def _g_cond_g1_313 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nLastToken-1+1]["sValue"].islower()
def _g_sugg_g1_125 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].capitalize()
def _g_cond_g1_314 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"] == "état"
def _g_cond_g1_315 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"] == "états"
def _g_cond_g1_316 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+3]["sValue"] == "état"
def _g_cond_g1_317 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+4]["sValue"] == "état"
def _g_cond_g1_318 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"][0:1] == "é"
def _g_sugg_g1_126 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("é", "É")
def _g_cond_g1_319 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].istitle() and g_morph(lToken[nTokenOffset], ":N", ":(?:A|V0e|D|R|B|X)")
def _g_sugg_g1_127 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].lower()
def _g_cond_g1_320 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].islower() and not lToken[nTokenOffset+1]["sValue"].startswith("canadienne") and ( g_value(lToken[nTokenOffset], "|certains|certaines|ce|cet|cette|ces|des|les|nos|vos|leurs|quelques|plusieurs|chaque|une|aux|la|ma|ta|sa|") or ( g_morph(lToken[nTokenOffset], ":B") and not g_morph(g_token(lToken, nTokenOffset+1-2), ">numéro/") ) or ( g_value(lToken[nTokenOffset], "|l’|") and g_morph(lToken[nTokenOffset+1], ":N.*:f:[si]") ) or ( g_value(lToken[nTokenOffset], "|de|d’|") and g_morph(g_token(lToken, nTokenOffset+1-2), ">(?:beaucoup|énormément|multitude|tant|tellement|poignée|groupe|car|bus|équipe|plus|moins|pas|trop|majorité|millier|million|centaine|dizaine|douzaine|combien|photo|complot|enlèvement|témoignage|viol|meurtre|assassinat|duel|tiers|quart|pourcentage|proportion|génération|portrait|rencontre|reportage|parole|communauté|vie|rassemblement|bataillon|armée|émigration|immigration|invasion|trio|couple|famille|descendante|action|attente|désir|souhait|vote|volonté)/") ) or ( g_value(lToken[nTokenOffset], "|un|") and not g_value(g_token(lToken, nTokenOffset+1-2), "|dans|numéro|") and not look(sSentence[lToken[nLastToken]["nEnd"]:], "(?:approximatif|correct|courant|parfait|facile|aisé|impeccable|incompréhensible)") ) )
def _g_sugg_g1_128 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].capitalize()
def _g_sugg_g1_129 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].capitalize()
def _g_cond_g1_321 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+3]["sValue"].isupper()
def _g_sugg_g1_130 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].lower()
def _g_cond_g1_322 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].islower() and lToken[nTokenOffset+2]["sValue"].islower()
def _g_cond_g1_323 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+4]["sValue"].islower()
def _g_sugg_g1_131 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].capitalize()
def _g_sugg_g1_132 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+4]["sValue"].capitalize()
def _g_cond_g1_324 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:D.*:p|R|C)")
def _g_cond_g1_325 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:d[eu]|avant|après|malgré)/")
def _g_cond_g1_326 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and hasFemForm(lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g1_133 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+4]["sValue"], True)
def _g_cond_g1_327 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":", ":(?:R|[123][sp]|Q)|>(?:[nv]ous|eux)/")
def _g_cond_g1_328 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and hasFemForm(lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g1_134 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+3]["sValue"], True)
def _g_sugg_g1_135 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+4]["sValue"], True)
def _g_sugg_g1_136 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+3]["sValue"], True)
def _g_sugg_g1_137 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+3]["sValue"], True)
def _g_cond_g1_329 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":R", ":D.*:p")
def _g_sugg_g1_138 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+2]["sValue"], True)
def _g_cond_g1_330 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":R")
def _g_sugg_g1_139 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+2]["sValue"], True)
def _g_sugg_g1_140 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+3]["sValue"], True)
def _g_cond_g1_331 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:f:p")
def _g_sugg_g1_141 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+2]["sValue"], True)
def _g_cond_g1_332 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":[NA].*:f:p")
def _g_cond_g1_333 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:f:s")
def _g_sugg_g1_142 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+2]["sValue"], True)
def _g_cond_g1_334 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":[NA].*:f:s")
def _g_cond_g1_335 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ">[aâeéêiîoôuœæ]")
def _g_cond_g1_336 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_analyse(lToken[nLastToken-1+1], ":V")
def _g_sugg_g1_143 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+3]["sValue"], ":E", ":2p")
def _g_cond_g1_337 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V")
def _g_sugg_g1_144 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":m:s")
def _g_sugg_g1_145 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":m:p")
def _g_sugg_g1_146 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":f:s")
def _g_sugg_g1_147 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":f:p")
def _g_cond_g1_338 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V[123].*:Iq.*:[32]s")
def _g_cond_g1_339 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|n’importe|ce|se|") and not g_morph(lToken[nTokenOffset], ":R")
def _g_sugg_g1_148 (lToken, nTokenOffset, nLastToken):
    return "l’a " + suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":m:s") + "|la " + lToken[nTokenOffset+3]["sValue"][:-2] + "ait"
def _g_da_g1_3 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":G:R:LR"])
def _g_cond_g1_340 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|que|qu’|")
def _g_cond_g1_341 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ne|n’|")
def _g_da_g1_4 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":LN:m:p"])
def _g_cond_g1_342 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NV]", ":A:[em]:[is]")
def _g_cond_g1_343 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|une|la|cet|cette|ma|ta|sa|notre|votre|leur|de|quelque|certaine|")
def _g_cond_g1_344 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":E")
def _g_da_g1_5 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+2], [">numéro/:N:f:s"])
def _g_cond_g1_345 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":[NA]", ":G", 0, -3)
def _g_tp_g1_3 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-3]
def _g_da_g1_6 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":B:e:p"])
def _g_cond_g1_346 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|d’|")
def _g_cond_g1_347 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NAQR]|>que/")
def _g_cond_g1_348 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NA]", ":V0")
def _g_cond_g1_349 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NA]", ":V0") and not g_morph(lToken[nLastToken+1], ":(?:Ov|3s)")
def _g_cond_g1_350 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NA]", ":V0") and not g_morph(lToken[nLastToken+1], ":(?:Ov|1p)")
def _g_cond_g1_351 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NA]", ":V0") and not g_morph(lToken[nLastToken+1], ":(?:Ov|2p)")
def _g_cond_g1_352 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NA]", ":V0") and not g_morph(lToken[nLastToken+1], ":(?:Ov|3p)")
def _g_cond_g1_353 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:[me]:[si]")
def _g_cond_g1_354 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":A")
def _g_cond_g1_355 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":Ov|>(?:il|on|elle)")
def _g_cond_g1_356 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|en|de|d’|")
def _g_cond_g1_357 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:X|Oo)") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_2s_")
def _g_cond_g1_358 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":N.*:[me]:[si]")
def _g_cond_g1_359 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":N.*:[fe]:[si]")
def _g_cond_g1_360 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":N.*:[me]:[pi]")
def _g_cond_g1_361 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":N.*:[fe]:[pi]")
def _g_cond_g1_362 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:D.*:p|N|V)")
def _g_cond_g1_363 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:f:[si]")
def _g_cond_g1_364 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:R|C[sc])")
def _g_cond_g1_365 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[AW]") and not g_morph(lToken[nTokenOffset], ":D")
def _g_cond_g1_366 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:V|N:f)", ":G")
def _g_cond_g1_367 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NV]", ":D.*:[fe]:[si]")
def _g_cond_g1_368 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_value(lToken[nTokenOffset], "|recettes|réponses|solutions|")
def _g_da_g1_7 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+1], ":N")
def _g_cond_g1_369 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":N") and not g_morph(lToken[nLastToken+1], ":A.*:[me]:[si]")
def _g_cond_g1_370 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":N") and not g_morph(lToken[nLastToken+1], ":A.*:[fe]:[si]")
def _g_cond_g1_371 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:N|A|Q|W|V0e)", ":D")
def _g_cond_g1_372 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[NA]", ":D")
def _g_cond_g1_373 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset], ":D|>(?:être|devenir|redevenir|rester|sembler|demeurer|para[îi]tre)")
def _g_da_g1_8 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+1], [":A:e:i"])
def _g_cond_g1_374 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].istitle() and g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) or re.search("^[MDCLXVI]+$", lToken[nTokenOffset+2]["sValue"])
def _g_cond_g1_375 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].istitle()
def _g_cond_g1_376 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+3]["sValue"].istitle()
def _g_cond_g1_377 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].istitle() and lToken[nTokenOffset+4]["sValue"].istitle()
def _g_cond_g1_378 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":M") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "\\b(?:plus|moins|aussi) .* que +$")
def _g_tp_g1_4 (lToken, nTokenOffset, nLastToken):
    return rewriteSubject(lToken[nTokenOffset+2]["sValue"],lToken[nTokenOffset+4]["sValue"]) + "||"
def _g_cond_g1_379 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":M")
def _g_cond_g1_380 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":1s")
def _g_cond_g1_381 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":2s")
def _g_cond_g1_382 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":3s")
def _g_cond_g1_383 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":1p")
def _g_cond_g1_384 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":2p")
def _g_cond_g1_385 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":3p")
def _g_da_g1_9 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+2], [":LV"])
def _g_da_g1_10 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+3], [":LV"])
def _g_cond_g1_386 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:être|devenir|rester)")
def _g_cond_g1_387 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":[QY]")
def _g_cond_g1_388 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:être|devenir|rester)") and g_morph(lToken[nLastToken+1], ":[QY]")
def _g_cond_g1_389 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:V0e|N)") and g_morph(lToken[nLastToken+1], ":[AQ]")
def _g_cond_g1_390 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V0a")
def _g_cond_g1_391 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V0a") and g_morph(lToken[nLastToken+1], ":[QY]")
def _g_cond_g1_392 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[VW]", ":G")
def _g_cond_g1_393 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V") and not g_value(lToken[nLastToken+1], "|qui|de|d’|")
def _g_cond_g1_394 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|qui|de|d’|")
def _g_cond_g1_395 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V")
def _g_cond_g1_396 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|de|d’|des|du|")
def _g_cond_g1_397 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":[AW]")
def _g_cond_g1_398 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|un|le|ce|du|mon|ton|son|notre|votre|leur|")
def _g_cond_g1_399 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (lToken[nTokenOffset+2]["sValue"] == "bien" and g_value(lToken[nLastToken+1], "|que|qu’|")) and not (lToken[nTokenOffset+2]["sValue"] == "tant" and g_value(lToken[nLastToken+1], "|est|"))
def _g_cond_g1_400 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":A", ":G")
def _g_cond_g1_401 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":W", ":3p")
def _g_cond_g1_402 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":W", ":A")
def _g_cond_g1_403 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:m")
def _g_cond_g1_404 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":W", ":(?:3p|N)")
def _g_cond_pp2_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":N", ":V")
def _g_cond_pp2_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|j’|tu|il|elle|on|n’")
def _g_cond_pp2_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ça|cela|ceci|me|m’|te|t’|lui|nous|vous|leur|ne|n’|")
def _g_cond_pp2_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D") and not g_morph(lToken[nLastToken+1], ":[NA].*:[fe]:[si]")
def _g_cond_pp2_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R|>d’/")
def _g_cond_pp2_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":[123]p") or (lToken[nTokenOffset+1]["sValue"] == "fait" and g_value(lToken[nTokenOffset], "|on|"))
def _g_cond_pp2_7 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":[123]p")
def _g_cond_pp2_8 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-2+1], ":[123]s")
def _g_cond_pp3_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-3+1], ":[123][sp]")
def _g_da_pp3_1 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nLastToken-2+1], ":D") and g_exclude(lToken[nLastToken-1+1], ":[123][sp]")
def _g_cond_pp3_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA]", ":(?:G|V0)") and g_morph(lToken[nTokenOffset+4], ":[NA]", ":(?:[PG]|V[023])")
def _g_da_pp3_2 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+4], ":V")
def _g_cond_pp3_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":p") and g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":(?:G|V0)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:p", ":(?:[PGQ]|V[023])")
def _g_cond_pp3_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+2], ":s") and g_morph(lToken[nTokenOffset+3], ":[NA].*:s", ":(?:G|V0)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:s", ":(?:[PGQ]|V[023])") and not g_morph(lToken[nTokenOffset+5], ":A.*:[si]")
def _g_da_pp3_3 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+3], ":V")
def _g_cond_pp3_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], ":O[vs]")
def _g_da_pp3_4 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+2], ":V") and g_exclude(lToken[nTokenOffset+3], ":V")
def _g_cond_pp3_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_morph(lToken[nTokenOffset], ":V0a") and g_value(lToken[nLastToken+1], "|fait|"))
def _g_da_pp3_5 (lToken, nTokenOffset, nLastToken):
    return g_define(lToken[nTokenOffset+2], [":LV"])
def _g_sugg_g2_1 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|et|ou|de|") and not g_value(lToken[nTokenOffset+2], "|air|") and not g_morph(lToken[nTokenOffset+3], ">seul/")
def _g_cond_g2_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":m", "*") and g_morph(lToken[nTokenOffset+3], ":f", "*")) or (g_morph(lToken[nTokenOffset+2], ":f", "*") and g_morph(lToken[nTokenOffset+3], ":m", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_2 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+3]["sValue"], False)
def _g_cond_g2_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and hasFemForm(lToken[nTokenOffset+2]["sValue"])
def _g_sugg_g2_3 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[si]", "*") and g_morph(lToken[nTokenOffset+3], ":p", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_4 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+3], "|air|") and not g_morph(lToken[nTokenOffset+4], ">seul/")
def _g_cond_g2_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+3], ":m", "*") and g_morph(lToken[nTokenOffset+4], ":f", "*")) or (g_morph(lToken[nTokenOffset+3], ":f", "*") and g_morph(lToken[nTokenOffset+4], ":m", "*")) ) and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"]) and not g_morph(lToken[nTokenOffset], ":[NA]")
def _g_sugg_g2_5 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+4]["sValue"], False)
def _g_cond_g2_7 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and hasFemForm(lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_6 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_8 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[si]", "*") and g_morph(lToken[nTokenOffset+4], ":p", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"]) and not g_morph(lToken[nTokenOffset], ":[NA]")
def _g_sugg_g2_7 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_9 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":(?:e|m|P|G|W|[123][sp]|Y)")
def _g_sugg_g2_8 (lToken, nTokenOffset, nLastToken):
    return suggLesLa(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_10 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and hasMasForm(lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_9 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+3]["sValue"], True)
def _g_cond_g2_11 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":[siGW]")
def _g_sugg_g2_10 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_12 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo
def _g_cond_g2_13 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":D")
def _g_cond_g2_14 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":(?:e|m|P|G|W|[123][sp]|Y)") or ( g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[me]") and g_morph(lToken[nTokenOffset+1], ":R", ">(?:e[tn]|ou)/") and not (g_morph(lToken[nTokenOffset+1], ":Rv") and g_morph(lToken[nTokenOffset+3], ":Y")) )
def _g_cond_g2_15 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+3], ":[NA].*:p", "*") or ( g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":[si]") and g_morph(lToken[nTokenOffset+1], ":[RC]", ">(?:e[tn]|ou)/") and not (g_morph(lToken[nTokenOffset+1], ":Rv") and g_morph(lToken[nTokenOffset+3], ":Y")) )
def _g_cond_g2_16 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":(?:e|m|P|G|W|Y)")
def _g_cond_g2_17 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":D") and not g_value(lToken[nTokenOffset], "|et|ou|de|") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_cond_g2_18 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[me]", ":(?:B|G|V0)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:f", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_19 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[si]", ":G") and g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":[GWsi]") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_20 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":D") and not g_morph(lToken[nTokenOffset], ":[NA]") and not lToken[nTokenOffset+4]["sValue"].startswith("seul")
def _g_cond_g2_21 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[me]", ":(?:B|G|V0|f)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:f", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g2_11 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+4]["sValue"], True)
def _g_cond_g2_22 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[si]", ":G") and g_morph(lToken[nTokenOffset+4], ":[NA].*:p", ":[GWsi]") and not apposition(lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g2_12 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_23 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":(?:e|f|P|G|W|M|[1-3][sp]|Y)")
def _g_sugg_g2_13 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+3]["sValue"], True)
def _g_cond_g2_24 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+3], ":[NA].*:p")
def _g_sugg_g2_14 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_25 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":(?:e|f|P|G|W|M|[1-3][sp]|Y)") or ( g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[Mfe]") and g_morph(lToken[nTokenOffset+1], ":[RC]", ">(?:e[tn]|ou)/") and not (g_morph(lToken[nTokenOffset+1], ":(?:Rv|C)") and g_morph(lToken[nTokenOffset+3], ":Y")) )
def _g_cond_g2_26 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+3], ":[NA].*:p", "*") or ( g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":[Msi]") and g_morph(lToken[nTokenOffset+1], ":[RC]", ">(?:e[tn]|ou)/") and not (g_morph(lToken[nTokenOffset+1], ":Rv") and g_morph(lToken[nTokenOffset+3], ":Y")) )
def _g_cond_g2_27 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[efPGWMY]")
def _g_cond_g2_28 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":D") and not g_value(lToken[nTokenOffset], "|et|ou|de|d’|") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_cond_g2_29 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[fe]", ":(?:B|G|V0)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:m", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_30 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":D") and not g_morph(lToken[nTokenOffset], ":[NA]|>(?:et|ou)/") and not lToken[nTokenOffset+4]["sValue"].startswith("seul")
def _g_cond_g2_31 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[fe]", ":(?:B|G|V0|m)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:m", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g2_15 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+4]["sValue"], True)
def _g_cond_g2_32 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[si]", ":G") and g_morph(lToken[nTokenOffset+4], ":[NA].*:p", ":[GWsi]") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g2_16 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_33 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:p", "*")
def _g_cond_g2_34 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:p", "*") or ( g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":[si]") and g_morph(lToken[nTokenOffset+1], ":[RC]", ">(?:e[tn]|ou)/") and not (g_morph(lToken[nTokenOffset+1], ":Rv") and g_morph(lToken[nTokenOffset+3], ":Y")) )
def _g_cond_g2_35 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":[siGW]")
def _g_cond_g2_36 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ((g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":(?:B|e|G|V0|f)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:f", "*")) or (g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ":(?:B|e|G|V0|m)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:m", "*"))) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_17 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+2]["sValue"], False)
def _g_cond_g2_37 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":[NA].*:i")
def _g_cond_g2_38 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ((g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":(?:B|e|G|V0|f)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:f", "*")) or (g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":(?:B|e|G|V0|m)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:m", "*"))) and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_39 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+3], ":[NA].*:i")
def _g_cond_g2_40 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|et|ou|") and g_morph(lToken[nTokenOffset+1], ":D") and g_morph(lToken[nTokenOffset+2], ":[NA].*:[si]", ":(?:[123][sp]|G)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[si]", ":(?:[123][sp]|G|P)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:p", "*") and lToken[nTokenOffset+4]["sValue"].islower()
def _g_cond_g2_41 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ":[GWme]")
def _g_cond_g2_42 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and hasMasForm(lToken[nTokenOffset+2]["sValue"])
def _g_sugg_g2_18 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+2]["sValue"], True)
def _g_cond_g2_43 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:p", ":[siGW]")
def _g_sugg_g2_19 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_44 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":[efGW]")
def _g_sugg_g2_20 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+2]["sValue"], True)
def _g_sugg_g2_21 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_45 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ":(?:e|m|G|W|V0|3s|Y)")
def _g_cond_g2_46 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":(?:e|m|G|W|V0|3s)")
def _g_sugg_g2_22 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+3]["sValue"], True)
def _g_cond_g2_47 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":(?:e|f|G|W|V0|3s|P)") and not ( lToken[nTokenOffset+2]["sValue"] == "demi" and g_morph(lToken[nLastToken+1], ":N.*:f", "*") )
def _g_cond_g2_48 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":(?:e|f|G|W|V0|3s)")
def _g_sugg_g2_23 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+3]["sValue"], True)
def _g_cond_g2_49 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|et|ou|d’|") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_cond_g2_50 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[si]", ":G") and g_morph(lToken[nTokenOffset+3], ":[NA].*:p", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_51 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[NA]|>(?:et|ou)/") and not lToken[nTokenOffset+4]["sValue"].startswith("seul")
def _g_cond_g2_52 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[si]", ":G") and g_morph(lToken[nTokenOffset+4], ":[NA].*:p", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_53 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"] != "fois" and g_morph(lToken[nTokenOffset+2], ":[NA].*:[si]", ":G") and g_morph(lToken[nTokenOffset+3], ":[NA].*:p", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_54 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+3]["sValue"] != "fois" and g_morph(lToken[nTokenOffset+3], ":[NA].*:[si]", ":G") and g_morph(lToken[nTokenOffset+4], ":[NA].*:p", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_55 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ":(?:3s|[GWme])")
def _g_cond_g2_56 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ":[GWme]") and g_morph(lToken[nTokenOffset+2], ":3s")
def _g_cond_g2_57 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ">[bcçdfgjklmnpqrstvwxz].+:[NA].*:m", ":[efGW]")
def _g_sugg_g2_24 (lToken, nTokenOffset, nLastToken):
    return suggCeOrCet(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_58 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f:s", ":[GWme]")
def _g_cond_g2_59 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|et|ou|de|d’|") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_cond_g2_60 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":D")
def _g_cond_g2_61 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ">[bcdfgjklmnpqrstvwxz].*:[NA].*:f", ":[GWme]")
def _g_sugg_g2_25 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("on", "a").replace("ON", "A")
def _g_cond_g2_62 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":(?:B|G|e|V0|f)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:f", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_63 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ">[aâeéèêiîoôuûyœæ].*:[NA].*:f", ":(?:B|G|e|V0|m)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:m", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_64 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":(?:B|G|e|V0|f)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:f", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_65 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ">[aâeéèêiîoôuûyœæ].*:[NA].*:f", ":(?:B|G|e|V0|m)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:m", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g2_26 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-1]+"on"
def _g_cond_g2_66 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and not re.search("(?i)^[aâeéèêiîoôuûyœæ]", lToken[nTokenOffset+2]["sValue"]) and hasFemForm(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_67 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NAQ].*:[fe]", ":(?:B|G|V0)") and g_morph(lToken[nTokenOffset+3], ":[NAQ].*:m", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_68 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NAQ].*:[si]", ":G") and g_morph(lToken[nTokenOffset+3], ":[NAQ].*:p", ":[GWsi]") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_69 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[NAQ]|>(?:et|ou)/") and not lToken[nTokenOffset+4]["sValue"].startswith("seul")
def _g_cond_g2_70 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NAQ].*:[fe]", ":(?:B|G|V0|m)") and g_morph(lToken[nTokenOffset+4], ":[NAQ].*:m", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_71 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NAQ].*:[si]", ":G") and g_morph(lToken[nTokenOffset+4], ":[NAQ].*:p", ":[GWsi]") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_72 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:p", ":[siG]") and not g_value(lToken[nLastToken+1], "|que|qu’|")
def _g_cond_g2_73 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|et|ou|") and g_morph(lToken[nTokenOffset+2], ":[NA].*:[si]") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[si]", ":(?:[123][sp]|G|P)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:p", "*") and lToken[nTokenOffset+4]["sValue"].islower()
def _g_cond_g2_74 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( g_morph(lToken[nTokenOffset+3], ":[NA].*:s", "*") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]")) ) or lToken[nTokenOffset+3]["sValue"] in aREGULARPLURAL
def _g_sugg_g2_27 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_75 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":D") and ( g_morph(lToken[nTokenOffset+3], ":[NA].*:s", "*") or (g_morph(lToken[nTokenOffset+3], ":[NA].*:s", ":[pi]|>avoir/") and g_morph(lToken[nTokenOffset+1], ":[RC]", ">(?:e[tn]|ou)/") and not (g_morph(lToken[nTokenOffset+1], ":Rv") and g_morph(lToken[nTokenOffset+3], ":Y"))) ) and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]")) and not (g_value(lToken[nTokenOffset+1], "|que|") and g_morph(lToken[nTokenOffset], ">tel/") and g_morph(lToken[nTokenOffset+3], ":3[sp]"))
def _g_cond_g2_76 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( g_morph(lToken[nTokenOffset+3], ":[NA].*:s", ":[ipYPGW]") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]")) ) or lToken[nTokenOffset+3]["sValue"] in aREGULARPLURAL
def _g_sugg_g2_28 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+3]["sValue"], True)
def _g_sugg_g2_29 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+2]["sValue"], True)
def _g_cond_g2_77 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[pi]") and g_morph(lToken[nTokenOffset+3], ":[NA].*:s", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"]) and not (g_value(lToken[nLastToken+1], "|et|,|") and g_morph(g_token(lToken, nLastToken+2), ":A"))
def _g_cond_g2_78 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":D") and not g_morph(lToken[nTokenOffset], ":[NA]") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_sugg_g2_30 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nTokenOffset+4]["sValue"], True)
def _g_cond_g2_79 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]") and g_morph(lToken[nTokenOffset+4], ":[NA].*:s", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"]) and not (g_value(lToken[nLastToken+1], "|et|,|") and g_morph(g_token(lToken, nLastToken+2), ":A"))
def _g_sugg_g2_31 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_80 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (g_morph(lToken[nTokenOffset+2], ":[NA].*:s", ":(?:[ipGW]|[123][sp])") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]"))) or lToken[nTokenOffset+2]["sValue"] in aREGULARPLURAL
def _g_sugg_g2_32 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_81 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (g_morph(lToken[nTokenOffset+2], ":[NA].*:s", ":[ipGW]") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]"))) or lToken[nTokenOffset+2]["sValue"] in aREGULARPLURAL
def _g_cond_g2_82 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ">[bcdfglklmnpqrstvwxz].*:m", ":f")
def _g_cond_g2_83 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].endswith("x") or lToken[nTokenOffset+1]["sValue"].endswith("X")
def _g_cond_g2_84 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo
def _g_cond_g2_85 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|et|ou|de|d’|au|aux|") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_cond_g2_86 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]") and g_morph(lToken[nTokenOffset+4], ":[NA].*:s", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"]) and not (g_value(lToken[nLastToken+1], "|et|,|") and g_morph(g_token(lToken, nLastToken+2), ":A")) and not (lToken[nTokenOffset+1]["sValue"].startswith("de") and g_value(lToken[nTokenOffset], "|un|une|"))
def _g_cond_g2_87 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:et|ou)/|:R") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_cond_g2_88 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (g_morph(lToken[nTokenOffset], ":(?:[VRBX]|Cs|LV)|>comme/|<start>|>,", "*") or g_morph(lToken[nTokenOffset+3], ":N", ":[AQ]")) and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_cond_g2_89 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":[fe]") and g_morph(lToken[nTokenOffset+3], ":[NA].*:f", "*")) or (g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ":[me]") and g_morph(lToken[nTokenOffset+3], ":[NA].*:m", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_90 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+3], ":G|>a/") and checkAgreement(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_da_g2_1 (lToken, nTokenOffset, nLastToken):
    return g_exclude(lToken[nTokenOffset+3], ":V")
def _g_cond_g2_91 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (g_morph(lToken[nTokenOffset+2], ":[NA].*:s", ":[ipGWP]") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]"))) or lToken[nTokenOffset+2]["sValue"] in aREGULARPLURAL
def _g_cond_g2_92 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":D") and g_morph(lToken[nTokenOffset+2], ":[NA].*:[pi]", ":(?:[123][sp]|G)") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]", ":(?:[123][sp]|G)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:s", "*") and lToken[nTokenOffset+4]["sValue"].islower()
def _g_cond_g2_93 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[pi]") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]", ":(?:[123][sp]|G)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:s", "*") and lToken[nTokenOffset+4]["sValue"].islower() and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\bune? de +$") and not lToken[nTokenOffset+4]["sValue"].startswith("seul")
def _g_cond_g2_94 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[pi]", "[123][sp]") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]", ":(?:[123][sp]|G)") and g_morph(lToken[nTokenOffset+4], ":[NA].*:s", "*") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\bune? de +$") and not lToken[nTokenOffset+4]["sValue"].startswith("seul")
def _g_cond_g2_95 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ":[emGWP]")
def _g_sugg_g2_33 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+2]["sValue"], True)
def _g_cond_g2_96 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( g_morph(lToken[nTokenOffset+2], ":[NA].*:s", ":(?:[ipGWP]|V0)") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]")) ) or lToken[nTokenOffset+1]["sValue"] in aREGULARPLURAL
def _g_cond_g2_97 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[emGW]")
def _g_cond_g2_98 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":[efGWP]")
def _g_sugg_g2_34 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+2]["sValue"], True)
def _g_cond_g2_99 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( g_morph(lToken[nTokenOffset+2], ":[NA].*:s", ":[ipGWP]") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":[NA]")) ) or lToken[nTokenOffset+2]["sValue"] in aREGULARPLURAL
def _g_cond_g2_100 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[efGW]")
def _g_cond_g2_101 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f:p", ":(?:V0|Oo|[NA].*:[me]:[si])")
def _g_cond_g2_102 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m:p", ":(?:V0|Oo|[NA].*:[me]:[si])")
def _g_cond_g2_103 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f:[si]", ":(?:V0|Oo|[NA].*:[me]:[si])")
def _g_cond_g2_104 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f:s", ":(?:V0|Oo|[NA].*:[me]:[pi])")
def _g_cond_g2_105 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m:s", ":(?:V0|Oo|[NA].*:[me]:[pi])")
def _g_cond_g2_106 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f:[pi]", ":(?:V0|Oo|[NA].*:[me]:[pi])")
def _g_cond_g2_107 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m:p", ":(?:V0|Oo|[NA].*:[fe]:[si])")
def _g_cond_g2_108 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f:p", ":(?:V0|Oo|[NA].*:[fe]:[si])")
def _g_cond_g2_109 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m:[si]", ":(?:V0|Oo|[NA].*:[fe]:[si])")
def _g_cond_g2_110 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m:s", ":(?:V0|Oo|[NA].*:[fe]:[pi])")
def _g_cond_g2_111 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f:s", ":(?:V0|Oo|[NA].*:[fe]:[pi])")
def _g_cond_g2_112 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m:[pi]", ":(?:V0|Oo|[NA].*:[fe]:[pi])")
def _g_cond_g2_113 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tel|telle|")
def _g_cond_g2_114 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tels|telles|")
def _g_sugg_g2_35 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-1]
def _g_cond_g2_115 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tel|telle|") and g_morph(lToken[nTokenOffset+4], ":[NA].*:[fe]", ":m")
def _g_cond_g2_116 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tel|telle|") and g_morph(lToken[nTokenOffset+4], ":[NA].*:f", ":[me]")
def _g_cond_g2_117 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tel|telle|") and g_morph(lToken[nTokenOffset+4], ":[NA].*:[me]", ":f")
def _g_cond_g2_118 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tel|telle|") and g_morph(lToken[nTokenOffset+4], ":[NA].*:m", ":[fe]")
def _g_cond_g2_119 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tels|telles|") and g_morph(lToken[nTokenOffset+4], ":[NA].*:f", ":[me]")
def _g_cond_g2_120 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|tels|telles|") and g_morph(lToken[nTokenOffset+4], ":[NA].*:m", ":[fe]")
def _g_cond_g2_121 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":[NA].*:m", ":[fe]")
def _g_cond_g2_122 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":[NA].*:f", ":[me]")
def _g_cond_g2_123 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[pi]", ":G") and g_morph(lToken[nTokenOffset+3], ":[NA].*:s", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"]) and not (g_value(lToken[nLastToken+1], "|et|,|") and g_morph(g_token(lToken, nLastToken+2), ":A"))
def _g_sugg_g2_36 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_124 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[NA]|>(?:et|ou)/") and not lToken[nTokenOffset+3]["sValue"].startswith("seul")
def _g_sugg_g2_37 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+4]["sValue"], True)
def _g_cond_g2_125 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]", ":G") and g_morph(lToken[nTokenOffset+4], ":[NA].*:s", "*") and not apposition(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"]) and not (g_value(lToken[nLastToken+1], "|et|,|") and g_morph(g_token(lToken, nLastToken+2), ":A")) and not (lToken[nTokenOffset+1]["sValue"].startswith("de") and g_value(lToken[nTokenOffset], "|un|une|"))
def _g_sugg_g2_38 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+4]["sValue"])
def _g_sugg_g2_39 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_40 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+4]["sValue"], True)
def _g_sugg_g2_41 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_126 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"] != "cents"
def _g_cond_g2_127 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":A.*:f")
def _g_sugg_g2_42 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nLastToken-1+1]["sValue"], True)
def _g_cond_g2_128 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nLastToken-1+1], ":A.*:p")
def _g_sugg_g2_43 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nLastToken-1+1]["sValue"])
def _g_cond_g2_129 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":A.*:m")
def _g_sugg_g2_44 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nLastToken-1+1]["sValue"], True)
def _g_sugg_g2_45 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nLastToken-1+1]["sValue"])
def _g_sugg_g2_46 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nLastToken-1+1]["sValue"], True)
def _g_cond_g2_130 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nLastToken-1+1], ":A.*:s")
def _g_sugg_g2_47 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nLastToken-1+1]["sValue"])
def _g_sugg_g2_48 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nLastToken-1+1]["sValue"], True)
def _g_sugg_g2_49 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nLastToken-1+1]["sValue"])
def _g_cond_g2_131 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|neuf|mille|") and ( (g_morph(lToken[nTokenOffset+2], ":[NA].*:s", "*") and not g_value(lToken[nTokenOffset+2], "|multiplié|divisé|janvier|février|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor|") ) or lToken[nTokenOffset+2]["sValue"] in aREGULARPLURAL) and not re.search("^[IVXLDM]+$", lToken[nTokenOffset+1]["sValue"])
def _g_cond_g2_132 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( g_morph(lToken[nTokenOffset+2], ":[NA].*:s", "*") and not g_morph(lToken[nTokenOffset], ":N.*:m:[is]") and not g_value(lToken[nTokenOffset+2], "|multiplié|divisé|janvier|février|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor|") ) or lToken[nTokenOffset+2]["sValue"] in aREGULARPLURAL
def _g_cond_g2_133 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|multiplié|divisé|") and (g_morph(lToken[nTokenOffset+2], ":[NA].*:s", "*") or lToken[nTokenOffset+1]["sValue"] in aREGULARPLURAL) and not g_value(lToken[nTokenOffset], "|le|un|ce|du|")
def _g_cond_g2_134 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and not g_value(lToken[nTokenOffset+2], "|Rois|Corinthiens|Thessaloniciens|")
def _g_cond_g2_135 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and not g_value(lToken[nTokenOffset], "|/|") and not re.search("^0*[01](?:,[0-9]+|)$", lToken[nTokenOffset+1]["sValue"]) and not g_morph(lToken[nTokenOffset], ":N") and ( (g_morph(lToken[nTokenOffset+2], ":[NA].*:s", "*") and not g_value(lToken[nTokenOffset+2], "|janvier|février|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor|")) or lToken[nTokenOffset+1]["sValue"] in aREGULARPLURAL )
def _g_cond_g2_136 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|fois|janvier|février|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|rue|route|ruelle|place|boulevard|avenue|allée|chemin|sentier|square|impasse|cour|quai|chaussée|côte|vendémiaire|brumaire|frimaire|nivôse|pluviôse|ventôse|germinal|floréal|prairial|messidor|thermidor|fructidor|") and not re.search("^0*[01](?:,[0-9]+|)$", lToken[nTokenOffset+1]["sValue"]) and not g_value(lToken[nTokenOffset], "|et|ou|de|d’|") and not g_morph(lToken[nTokenOffset+3], ">(?:seule|maximum|minimum)/")
def _g_cond_g2_137 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[pi]", "*") and g_morph(lToken[nTokenOffset+3], ":[NA].*:s", "*") and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"]) and not (g_value(lToken[nLastToken+1], "|et|,|") and g_morph(g_token(lToken, nLastToken+2), ":A"))
def _g_sugg_g2_50 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"][:-1]
def _g_cond_g2_138 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ((g_morph(lToken[nTokenOffset+2], ":m", "*") and g_morph(lToken[nTokenOffset+3], ":f", "*")) or (g_morph(lToken[nTokenOffset+2], ":f", "*") and g_morph(lToken[nTokenOffset+3], ":m", "*"))) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_139 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ((g_morph(lToken[nTokenOffset+2], ":s", "*") and g_morph(lToken[nTokenOffset+3], ":p", "*")) or (g_morph(lToken[nTokenOffset+2], ":p", "*") and g_morph(lToken[nTokenOffset+3], ":s", "*"))) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_51 (lToken, nTokenOffset, nLastToken):
    return switchPlural(lToken[nTokenOffset+3]["sValue"])
def _g_sugg_g2_52 (lToken, nTokenOffset, nLastToken):
    return switchPlural(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_140 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":p") and g_morph(lToken[nTokenOffset+3], ":[pi]") and g_morph(lToken[nTokenOffset+4], ":s") and lToken[nTokenOffset+4]["sValue"].islower()
def _g_sugg_g2_53 (lToken, nTokenOffset, nLastToken):
    return switchPlural(lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_141 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":i") and g_morph(lToken[nTokenOffset+3], ":p")    and g_morph(lToken[nTokenOffset+4], ":s") and lToken[nTokenOffset+4]["sValue"].islower()
def _g_cond_g2_142 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":s") and g_morph(lToken[nTokenOffset+3], ":[si]") and g_morph(lToken[nTokenOffset+4], ":p") and lToken[nTokenOffset+4]["sValue"].islower()
def _g_cond_g2_143 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":i") and g_morph(lToken[nTokenOffset+3], ":s")    and g_morph(lToken[nTokenOffset+4], ":p") and lToken[nTokenOffset+4]["sValue"].islower()
def _g_cond_g2_144 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":p", "*") and g_morph(lToken[nTokenOffset+3], ":s", "*")) or (g_morph(lToken[nTokenOffset+2], ":s", "*") and g_morph(lToken[nTokenOffset+3], ":p", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_145 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":m", ":[fe]") and g_morph(lToken[nTokenOffset+3], ":f", "*")) or (g_morph(lToken[nTokenOffset+2], ":f", ":[me]") and g_morph(lToken[nTokenOffset+3], ":m", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_146 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":p", ":[si]") and g_morph(lToken[nTokenOffset+3], ":s", "*")) or (g_morph(lToken[nTokenOffset+2], ":s", ":[pi]") and g_morph(lToken[nTokenOffset+3], ":p", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_147 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":m", ":[fe]") and g_morph(lToken[nTokenOffset+3], ":f", "*")) or (g_morph(lToken[nTokenOffset+2], ":f", ":[me]") and g_morph(lToken[nTokenOffset+3], ":m", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"]) and not g_morph(lToken[nTokenOffset], ":[NA]|>(?:et|ou)/")
def _g_cond_g2_148 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":p", ":[si]") and g_morph(lToken[nTokenOffset+3], ":s", "*")) or (g_morph(lToken[nTokenOffset+2], ":s", ":[pi]") and g_morph(lToken[nTokenOffset+3], ":p", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"]) and not g_morph(lToken[nTokenOffset], ":[NA]|>(?:et|ou)/")
def _g_cond_g2_149 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":m", ":[fe]") and g_morph(lToken[nTokenOffset+3], ":f", "*")) or (g_morph(lToken[nTokenOffset+2], ":f", ":[me]") and g_morph(lToken[nTokenOffset+3], ":m", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"]) and g_morph(lToken[nTokenOffset], ":[VRX]|<start>")
def _g_cond_g2_150 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( (g_morph(lToken[nTokenOffset+2], ":p", ":[si]") and g_morph(lToken[nTokenOffset+3], ":s", "*")) or (g_morph(lToken[nTokenOffset+2], ":s", ":[pi]") and g_morph(lToken[nTokenOffset+3], ":p", "*")) ) and not apposition(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"]) and g_morph(lToken[nTokenOffset], ":[VRX]|<start>")
def _g_cond_g2_151 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+3]["sValue"].islower()
def _g_cond_g2_152 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+6], ":[NA].*:(?:m|f:p)", ":(?:G|P|[fe]:[is]|V0|3[sp])") and g_morph(lToken[nTokenOffset+5], ":[NA].*:[fe]") and not apposition(lToken[nTokenOffset+5]["sValue"], lToken[nTokenOffset+6]["sValue"])
def _g_sugg_g2_54 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+6]["sValue"], True)
def _g_cond_g2_153 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+6], ":[NA].*:(?:f|m:p)", ":(?:G|P|[me]:[is]|V0|3[sp])") and g_morph(lToken[nTokenOffset+5], ":[NA].*:[me]") and not apposition(lToken[nTokenOffset+5]["sValue"], lToken[nTokenOffset+6]["sValue"])
def _g_sugg_g2_55 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+6]["sValue"], True)
def _g_cond_g2_154 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":[NA].*:(?:f|m:p)", ":(?:G|P|[me]:[is]|V0|3[sp])") and g_morph(lToken[nTokenOffset+4], ":[NA].*:[me]") and not apposition(lToken[nTokenOffset+4]["sValue"], lToken[nTokenOffset+5]["sValue"])
def _g_sugg_g2_56 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+5]["sValue"], True)
def _g_cond_g2_155 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":", ":[NA].*:f|>[aéeiou].*:e") and g_morph(lToken[nTokenOffset+6], ":[NA].*:(?:f|m:p)", ":(?:G|P|m:[is]|V0|3[sp])") and not apposition(lToken[nTokenOffset+5]["sValue"], lToken[nTokenOffset+6]["sValue"])
def _g_cond_g2_156 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":G|>[aéeiou].*:[ef]") and g_morph(lToken[nLastToken-1+1], ":[NA].*:(?:f|m:p)", ":(?:G|P|[me]:[is]|V0|3[sp])") and not apposition(lToken[nLastToken-2+1]["sValue"], lToken[nLastToken-1+1]["sValue"])
def _g_cond_g2_157 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m", ":G|>[aéeiou].*:[ef]") and not g_morph(lToken[nLastToken-2+1], ":[NA].*:f|>[aéeiou].*:e") and g_morph(lToken[nLastToken-1+1], ":[NA].*:(?:f|m:p)", ":(?:G|P|[me]:[is]|V0|3[sp])") and not apposition(lToken[nLastToken-2+1]["sValue"], lToken[nLastToken-1+1]["sValue"])
def _g_cond_g2_158 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":[NA].*:s", ":(?:G|P|[me]:[ip]|V0|3[sp])") and g_morph(lToken[nLastToken-2+1], ":[NA].*:[pi]") and not apposition(lToken[nLastToken-2+1]["sValue"], lToken[nLastToken-1+1]["sValue"])
def _g_sugg_g2_57 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nLastToken-1+1]["sValue"])
def _g_cond_g2_159 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+4], "|bâtiment|collège|corps|culte|établissement|groupe|journal|lycée|pays|régiment|vaisseau|village|")
def _g_sugg_g2_58 (lToken, nTokenOffset, nLastToken):
    return "leurs " + suggPlur(lToken[nTokenOffset+4]["sValue"])
def _g_cond_g2_160 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+4], "|armée|cité|compagnie|entreprise|église|fac|nation|université|planète|promotion|religion|unité|ville|")
def _g_cond_g2_161 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:m:[si]", ":f") and g_morph(lToken[nTokenOffset+4], ":R", ">à/")
def _g_cond_g2_162 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:f:[si]", ":m") and g_morph(lToken[nTokenOffset+4], ":R", ">à/")
def _g_cond_g2_163 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:m:[pi]", ":f") and g_morph(lToken[nTokenOffset+4], ":R", ">à/")
def _g_cond_g2_164 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:f:[pi]", ":m") and g_morph(lToken[nTokenOffset+4], ":R", ">à/")
def _g_cond_g2_165 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:m:[si]", ":f")
def _g_cond_g2_166 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:m:[si]", ":f:[si]")
def _g_cond_g2_167 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:f:[si]", ":m")
def _g_cond_g2_168 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:m:[pi]")
def _g_cond_g2_169 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:f:[pi]", ":m")
def _g_cond_g2_170 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":R") and g_morph(lToken[nTokenOffset+4], ":N.*:m:[pi]", ":f:[pi]")
def _g_cond_g2_171 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":R") and g_morph(lToken[nTokenOffset+4], ":N.*:f:[pi]", ":m:[pi]")
def _g_cond_g2_172 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:m:[pi]", ":f:[pi]")
def _g_cond_g2_173 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:f:[pi]", ":m:[pi]")
def _g_cond_g2_174 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":N", ":[GAVWM]")
def _g_cond_g2_175 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":N", ":D") and (not g_morph(lToken[nTokenOffset+1], ":[me]:[si]") or g_morph(lToken[nTokenOffset+2], ":[pf]"))
def _g_sugg_g2_59 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+1]["sValue"]) + " " + suggMasSing(lToken[nTokenOffset+2]["sValue"])
def _g_sugg_g2_60 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+1]["sValue"]) + " " + suggMasSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_176 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":N", ":D") and (not g_morph(lToken[nTokenOffset+1], ":[me]:[si]") or g_morph(lToken[nTokenOffset+2], ":p"))
def _g_sugg_g2_61 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+1]["sValue"]) + " " + suggSing(lToken[nTokenOffset+2]["sValue"])
def _g_sugg_g2_62 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+1]["sValue"]) + " " + suggSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_177 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D")
def _g_sugg_g2_63 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nLastToken-2+1]["sValue"])
def _g_cond_g2_178 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|quatre|")
def _g_cond_g2_179 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":B") and not g_morph(lToken[nTokenOffset], ">(?:numéro|page|chapitre|référence|année|test|série)/")
def _g_sugg_g2_64 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("vingts", "vingt").replace("VINGTS", "VINGT")
def _g_cond_g2_180 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken+1], ":B|>une?") and not g_morph(lToken[nTokenOffset], ">(?:numéro|page|chapitre|référence|année|test|série)/")
def _g_cond_g2_181 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":B|>une?")
def _g_cond_g2_182 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[VR]|<start>", ":B")
def _g_cond_g2_183 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":(?:B|N.*:p)", ":[QA]") or (g_morph(lToken[nTokenOffset], ":B") and g_morph(lToken[nLastToken+1], ":[NA]"))
def _g_cond_g2_184 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (g_morph(lToken[nTokenOffset+3], ":[NA].*:s", ":[ip]|>o(?:nde|xydation|r)/") and g_morph(lToken[nTokenOffset], ":(?:G|[123][sp])|<start>", ":[AD]")) or lToken[nTokenOffset+3]["sValue"] in aREGULARPLURAL
def _g_cond_g2_185 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":[NA].*:s", ":[ip]|>fraude/") or lToken[nTokenOffset+4]["sValue"] in aREGULARPLURAL
def _g_cond_g2_186 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D|<start>")
def _g_sugg_g2_65 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"][:-1]
def _g_cond_g2_187 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":(?:N|MP)")
def _g_sugg_g2_66 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-2]+"s"
def _g_cond_g2_188 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V.*:[123]|>(?:tou(?:te|)s|pas|rien|guère|jamais|toujours|souvent)/", ":[DRB]")
def _g_cond_g2_189 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+1]["sValue"].islower() and g_morph(lToken[nTokenOffset], ":V", ":[DA]") and not g_morph(lToken[nLastToken+1], ":[NA].*:[pi]") and not (g_morph(lToken[nTokenOffset], ">(?:être|sembler|devenir|rester|demeurer|redevenir|para[îi]tre|trouver)/.*:[123]p") and g_morph(lToken[nLastToken+1], ":G|<end>|>,/"))
def _g_cond_g2_190 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\b(?:lit|fauteuil|armoire|commode|guéridon|tabouret|chaise)s?\\b") and not g_morph(lToken[nLastToken+1], ">sculpter/")
def _g_cond_g2_191 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:V|R|[NAQ].*:s)", ":(?:[NA].*:[pi]|V0e.*:[123]p)")
def _g_cond_g2_192 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:f:s")
def _g_cond_g2_193 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":V0e.*:3p") or g_morph(lToken[nLastToken+1], ":[AQ]")
def _g_cond_g2_194 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"] != "clair" and lToken[nTokenOffset+2]["sValue"] != "Claire"
def _g_cond_g2_195 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V")
def _g_cond_g2_196 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V", ":[AN].*:[me]:[pi]|>(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre|appara[îi]tre)/.*:(?:[123]p|P|Q|Y)|>(?:affirmer|trouver|croire|désirer|estimer|préférer|penser|imaginer|voir|vouloir|aimer|adorer|rendre|souhaiter)/") and not g_morph(lToken[nLastToken+1], ":A.*:[me]:[pi]")
def _g_cond_g2_197 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V", ":[AN].*:[me]:[pi]|>(?:être|sembler|devenir|re(?:ster|devenir)|para[îi]tre|appara[îi]tre)/.*:(?:[123]p|P|Q|Y)")
def _g_cond_g2_198 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":V", ":[DA].*:p")
def _g_cond_g2_199 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nLastToken-1+1]["sValue"] != "A" and not g_tag_before(lToken[nTokenOffset+1], dTags, "_àCOI_") and not g_value(lToken[nLastToken+1], "|été|")
def _g_cond_g2_200 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_propsub_") and not g_morph(lToken[nTokenOffset+1], ":Y") and not g_value(lToken[nLastToken+1], "|été|")
def _g_cond_g2_201 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nLastToken-1+1]["sValue"] != "A" and not g_tag_before(lToken[nTokenOffset+1], dTags, "_propsub_") and not g_morph(lToken[nLastToken+1], ":Q")
def _g_cond_g2_202 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|rendez-vous|")
def _g_cond_g2_203 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":Cs|<start>|>,")
def _g_sugg_g2_67 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("â", "a").replace("Â", "A")
def _g_sugg_g2_68 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("a", "â").replace("A", "Â")
def _g_sugg_g2_69 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("oc", "o")
def _g_sugg_g2_70 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("oc", "o")
def _g_sugg_g2_71 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("ro", "roc")
def _g_cond_g2_204 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">faire")
def _g_sugg_g2_72 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("auspice", "hospice")
def _g_sugg_g2_73 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("auspice", "hospice").replace("Auspice", "Hospice")
def _g_sugg_g2_74 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("âill", "ay").replace("aill", "ay").replace("ÂILL", "AY").replace("AILL", "AY")
def _g_sugg_g2_75 (lToken, nTokenOffset, nLastToken):
    return "arrière-"+lToken[nTokenOffset+2]["sValue"].replace("c", "").replace("C", "")
def _g_sugg_g2_76 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("c", "").replace("C", "")
def _g_cond_g2_205 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +des accusés")
def _g_sugg_g2_77 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("an", "anc").replace("AN", "ANC")
def _g_sugg_g2_78 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("an", "anc").replace("AN", "ANC")
def _g_cond_g2_206 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (g_morph(lToken[nLastToken+1], ":[AQR]") or g_morph(lToken[nTokenOffset], ":V", ">être")) and not g_value(lToken[nLastToken+1], "|que|qu’|sûr|")
def _g_sugg_g2_79 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ite", "itte")
def _g_sugg_g2_80 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("itte", "ite")
def _g_sugg_g2_81 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("itte", "ite")
def _g_cond_g2_207 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":C|<start>") or g_value(lToken[nTokenOffset], "|,|")
def _g_sugg_g2_82 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ane", "anne")
def _g_sugg_g2_83 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+4]["sValue"].replace("ane", "anne")
def _g_cond_g2_208 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+3], "|Cannes|CANNES|")
def _g_cond_g2_209 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A")
def _g_sugg_g2_84 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("omp", "on").replace("OMP", "ON")
def _g_cond_g2_210 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|ils|elles|iels|ne|eux|")
def _g_sugg_g2_85 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("nt", "mp")
def _g_cond_g2_211 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|l’|un|les|des|ces|")
def _g_sugg_g2_86 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("sens", "cens").replace("Sens", "Cens").replace("SENS", "CENS")
def _g_sugg_g2_87 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("cens", "sens").replace("Cens", "Sens").replace("CENS", "SENS")
def _g_cond_g2_212 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[VR]")
def _g_sugg_g2_88 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("o", "ô").replace("tt", "t")
def _g_sugg_g2_89 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ô", "o").replace("tt", "t")
def _g_sugg_g2_90 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ô", "o").replace("t", "tt")
def _g_sugg_g2_91 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("t", "tt").replace("T", "TT")
def _g_cond_g2_213 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:f")
def _g_sugg_g2_92 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("tt", "t").replace("TT", "T")
def _g_sugg_g2_93 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ssa", "ça").replace("ss", "c")
def _g_cond_g2_214 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":Q")
def _g_sugg_g2_94 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("nud", "nu").replace("NUD", "NU")
def _g_sugg_g2_95 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("escell", "écel").replace("essell", "écel")
def _g_sugg_g2_96 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("escell", "écel").replace("essell", "écel")
def _g_cond_g2_215 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ">(?:être|voyager|surprendre|venir|arriver|partir|aller)/") or look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "-(?:ils?|elles?|on|je|tu|nous|vous) +$")
def _g_cond_g2_216 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_value(lToken[nTokenOffset], "|avec|sans|quel|quelle|quels|quelles|cet|votre|notre|mon|leur|l’|d’|")
def _g_cond_g2_217 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower()
def _g_sugg_g2_97 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("imm", "ém").replace("Imm", "Ém")
def _g_cond_g2_218 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D")
def _g_sugg_g2_98 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("imm", "ém").replace("Imm", "Ém")
def _g_sugg_g2_99 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("émi", "immi").replace("Émi", "Immi")
def _g_sugg_g2_100 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("end", "ind").replace("End", "Ind").replace("END", "IND")
def _g_sugg_g2_101 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("end", "ind").replace("End", "Ind").replace("END", "IND")
def _g_sugg_g2_102 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ind", "end").replace("Ind", "End").replace("IND", "END")
def _g_cond_g2_219 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C||>,/") and g_morph(lToken[nTokenOffset+2], ":N", ":[AG]")
def _g_cond_g2_220 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C||>,/") and g_morph(lToken[nTokenOffset+2], ":N.*:[fe]")
def _g_cond_g2_221 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C||>,/") and g_morph(lToken[nTokenOffset+2], ":N", ":A.*:[me]:[si]")
def _g_cond_g2_222 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C||>,/") and g_morph(lToken[nTokenOffset+2], ":[NA]") and g_morph(lToken[nTokenOffset+3], ":N", ":[AG]")
def _g_cond_g2_223 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C||>,/") and g_morph(lToken[nTokenOffset+2], ":[NA].*:[fe]:[si]") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[fe]:[si]")
def _g_cond_g2_224 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|:C||>,/") and ( (g_morph(lToken[nTokenOffset+2], ":N", "*") and g_morph(lToken[nTokenOffset+3], ":A")) or (g_morph(lToken[nTokenOffset+2], ":[NA]") and g_morph(lToken[nTokenOffset+3], ":N", ":A.*:[me]:[si]")) )
def _g_cond_g2_225 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:abandonner|céder|résister)/") and not g_value(lToken[nLastToken+1], "|de|d’|")
def _g_cond_g2_226 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[is]", ":G") and g_morph(lToken[nLastToken-2+1], ":[QA]", ":M") and lToken[nLastToken-2+1]["sValue"].islower()
def _g_cond_g2_227 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N.*:[is]", ":[GA]") and g_morph(lToken[nLastToken-2+1], ":[QA]", ":M") and lToken[nLastToken-2+1]["sValue"].islower()
def _g_cond_g2_228 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":M", ":[GA]") and g_morph(lToken[nLastToken-2+1], ":[QA]", ":M") and lToken[nLastToken-2+1]["sValue"].islower()
def _g_cond_g2_229 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":N.*:m:[si]", ":(?:[AWG]|V0a)") and g_morph(lToken[nTokenOffset], ":Cs|<start>|>,")
def _g_cond_g2_230 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":N.*:f:[si]", ":(?:[AWG]|V0a)") and g_morph(lToken[nTokenOffset], ":Cs|<start>|>,")
def _g_cond_g2_231 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":N.*:[pi]", ":(?:[AWG]|V0a)") and g_morph(lToken[nTokenOffset], ":Cs|<start>|>,")
def _g_cond_g2_232 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R")
def _g_cond_g2_233 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":D.*:[me]:[sp]")
def _g_sugg_g2_103 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("î", "i")
def _g_cond_g2_234 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_2p_")
def _g_sugg_g2_104 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("n", "nc").replace("N", "NC")
def _g_sugg_g2_105 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("and", "ant")
def _g_cond_g2_235 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset], "|une|") and look(sSentence[lToken[nLastToken]["nEnd"]:], "(?i)^ +pour toute") )
def _g_cond_g2_236 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":D.*:(?:f|e:p)")
def _g_sugg_g2_106 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("iai", "iè")
def _g_sugg_g2_107 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("iè", "iai")
def _g_sugg_g2_108 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("û", "u").replace("t", "tt")
def _g_cond_g2_237 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-2+1], "|de|")
def _g_sugg_g2_109 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("outt", "oût").replace("OUTT", "OÛT")
def _g_sugg_g2_110 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("oût", "outt").replace("OÛT", "OUTT").replace("out", "outt").replace("OUT", "OUTT")
def _g_sugg_g2_111 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("outt", "oût").replace("OUTT", "OÛT")
def _g_cond_g2_238 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken-1+1], ":1p")
def _g_cond_g2_239 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken-1+1], ":2p")
def _g_sugg_g2_112 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("u", "û").replace("U", "Û")
def _g_sugg_g2_113 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("û", "u").replace("Û", "U")
def _g_sugg_g2_114 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][3:]
def _g_sugg_g2_115 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].lower().replace("cha", "lâ")
def _g_cond_g2_240 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":Q")
def _g_cond_g2_241 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 4)
def _g_sugg_g2_116 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("a", "â").replace("A", "Â")
def _g_sugg_g2_117 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ât", "at").replace("ÂT", "AT")
def _g_sugg_g2_118 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("u", "û").replace("U", "Û")
def _g_cond_g2_242 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":D", ">de/")
def _g_sugg_g2_119 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("en", "an").replace("EN", "AN")
def _g_sugg_g2_120 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("an", "en").replace("AN", "EN")
def _g_sugg_g2_121 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("a", "â").replace("A", "Â")
def _g_cond_g2_243 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-3+1], ":V")
def _g_sugg_g2_122 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("êch", "éch").replace("er", "é").replace("ÊCH", "ÉCH").replace("ER", "É")
def _g_sugg_g2_123 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("éch", "êch").replace("èch", "êch").replace("ÉCH", "ÊCH").replace("ÈCH", "ÊCH")
def _g_cond_g2_244 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|je|tu|il|elle|on|ne|n’|") and g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 3)
def _g_cond_g2_245 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N")
def _g_cond_g2_246 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nLastToken-1+1], ":V1..t") and g_morph(lToken[nLastToken+1], ":(?:Ov|[123][sp]|P)|<end>|>(?:,|par)/")
def _g_sugg_g2_124 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":m:s")
def _g_sugg_g2_125 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":f:s")
def _g_sugg_g2_126 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":s")
def _g_cond_g2_247 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA]") and g_morph(lToken[nTokenOffset+4], ":[NA]", ":V0")
def _g_cond_g2_248 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":V", ":[NAQGM]")
def _g_cond_g2_249 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1)
def _g_sugg_g2_127 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("t", "g").replace("T", "G")
def _g_cond_g2_250 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A") and g_morph(lToken[nTokenOffset], ":D")
def _g_sugg_g2_128 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("t", "g").replace("T", "G")
def _g_cond_g2_251 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|n’|")
def _g_cond_g2_252 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1)
def _g_sugg_g2_129 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("out", "oot").replace("OUT", "OOT")
def _g_sugg_g2_130 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ô", "o").replace("Ô", "O")
def _g_sugg_g2_131 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("od", "ôd").replace("OD", "ÔD")
def _g_sugg_g2_132 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("ale", "alle")
def _g_sugg_g2_133 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("alle", "ale")
def _g_sugg_g2_134 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("scep","sep")
def _g_cond_g2_253 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">plaie/")
def _g_sugg_g2_135 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("sep", "scep")
def _g_cond_g2_254 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_analyse(lToken[nTokenOffset+3], ":N.*:[me]:[si]", ":Y")
def _g_cond_g2_255 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_analyse(lToken[nTokenOffset+3], ":[NA]", ":Y")
def _g_cond_g2_256 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], " soit ")
def _g_cond_g2_257 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "[aA]ccompl|[dD]él[éè]gu")
def _g_sugg_g2_136 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("â", "a").replace("Â", "A")
def _g_sugg_g2_137 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"].replace("â", "a").replace("Â", "A")
def _g_sugg_g2_138 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("a", "â").replace("A", "Â")
def _g_cond_g2_258 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":D", ":R")
def _g_sugg_g2_139 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"].replace("ach", "âch").replace("ACH", "ÂCH")
def _g_sugg_g2_140 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("au", "ô").replace("AU", "Ô")
def _g_sugg_g2_141 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("énén", "enim").replace("ÉNÉN", "ENIM")
def _g_sugg_g2_142 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("enim", "énén").replace("ENIM", "ÉNÉN")
def _g_cond_g2_259 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ":3[sp]")
def _g_sugg_g2_143 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+2]["sValue"], ":3s")
def _g_cond_g2_260 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+3], ":3[sp]")
def _g_sugg_g2_144 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3s")
def _g_sugg_g2_145 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3p")
def _g_cond_g2_261 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">être/")
def _g_cond_g2_262 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nLastToken-1+1]["sValue"].islower()
def _g_sugg_g2_146 (lToken, nTokenOffset, nLastToken):
    return suggVerbInfi(lToken[nLastToken-1+1]["sValue"])
def _g_cond_g2_263 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V", ":M") and not (lToken[nLastToken-1+1]["sValue"].endswith("ez") and g_value(lToken[nLastToken+1], "|vous|"))
def _g_cond_g2_264 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+1], ":N") and (g_analyse(lToken[nLastToken-1+1], ":V1.*:Q", ":(?:M|Oo)") or g_analyse(lToken[nLastToken-1+1], ":[123][sp]", ":[MNG]"))
def _g_cond_g2_265 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_analyse(lToken[nLastToken-1+1], ":Q", ":M")
def _g_cond_g2_266 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_analyse(lToken[nLastToken-1+1], ":Q", ":[MN]")
def _g_cond_g2_267 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|une|la|cette|ma|ta|sa|notre|votre|leur|quelle|de|d’|") and g_analyse(lToken[nLastToken-1+1], ":Q", ":M")
def _g_cond_g2_268 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"][0:1].isupper() and not g_morph(lToken[nTokenOffset], ">(?:en|passer|qualifier)/") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)(?:quelqu(?:e chose|’une?)|qu’y a-t-il |\\b(?:l(?:es?|a)|nous|vous|me|te|se) trait|personne|points? +$|autant +$|ça +|rien d(?:e |’)|rien(?: +[a-zéèêâîûù]+|) +$)") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_")
def _g_sugg_g2_147 (lToken, nTokenOffset, nLastToken):
    return suggVerbInfi(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_269 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V", ":[123][sp]")
def _g_cond_g2_270 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 3) and g_morph(lToken[nTokenOffset+2], ":Q") and not g_morph(lToken[nTokenOffset], "V0.*[12]p")
def _g_cond_g2_271 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V", ":M") and not (g_morph(lToken[nTokenOffset+1], ":N") and g_morph(lToken[nTokenOffset], ":D")) and not (g_value(lToken[nTokenOffset+1], "|devant|") and g_morph(lToken[nLastToken-1+1], ":N"))
def _g_cond_g2_272 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|puis|") and g_morph(lToken[nLastToken-1+1], ":V", ":M") and not (g_morph(lToken[nTokenOffset+1], ":N") and g_morph(lToken[nTokenOffset], ":D"))
def _g_cond_g2_273 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|me|m’|te|t’|se|s’|le|la|l’|les|") and g_morph(lToken[nLastToken-1+1], ":V", ":M") and not (g_morph(lToken[nTokenOffset+1], ":N") and g_morph(lToken[nTokenOffset], ":D"))
def _g_cond_g2_274 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V", ":M")
def _g_cond_g2_275 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:devoir|savoir|pouvoir|vouloir)/") and g_morph(lToken[nLastToken-1+1], ":(?:Q|A|[123][sp])", ":[GYW]")
def _g_cond_g2_276 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:devoir|savoir|pouvoir|vouloir)/") and g_morph(lToken[nLastToken-1+1], ":(?:Q|A|[123][sp])", ":[GYWN]")
def _g_cond_g2_277 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V", ":[NGMY]") and not lToken[nTokenOffset+3]["sValue"][0:1].isupper()
def _g_sugg_g2_148 (lToken, nTokenOffset, nLastToken):
    return suggVerbInfi(lToken[nTokenOffset+3]["sValue"])
def _g_cond_g2_278 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V1")
def _g_cond_g2_279 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|que|qu’|")
def _g_cond_g2_280 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and g_morph(lToken[nLastToken-1+1], ":3[sp]"))
def _g_cond_g2_281 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:en|de|être)/") and g_morph(lToken[nTokenOffset+2], ":V", ":[MG]") and not (g_morph(lToken[nTokenOffset+1], ":N") and g_morph(lToken[nTokenOffset+2], ":Q.*:m:[sp]"))
def _g_cond_g2_282 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V1.*:(?:Q|Ip.*:2p|Iq.*:[123]s)", ">désemparer/.*:Q")
def _g_cond_g2_283 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|Ip.*:2p|Iq.*:[123]s)", ">désemparer/.*:Q|:N")
def _g_cond_g2_284 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|Ip.*:2p|Iq.*:[123]s)", ">désemparer/.*:Q")
def _g_cond_g2_285 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ":N") and g_morph(lToken[nTokenOffset+3], ":V1.*:(?:Q|Ip.*:2p)", ">désemparer/.*:Q")
def _g_cond_g2_286 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ":N") and g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|Ip.*:2p|Iq.*:[123]s)", ">désemparer/.*:Q|:N")
def _g_cond_g2_287 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+2], ":N") and g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|Ip.*:2p|Iq.*:[123]s)", ">désemparer/.*:Q")
def _g_cond_g2_288 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">laisser") and (g_morph(lToken[nTokenOffset+2], ":V1.*:(?:Q|Ip.*:2[sp])", ">désemparer/.*:Q") or (not g_morph(lToken[nTokenOffset], ":D") and g_morph(lToken[nLastToken-1+1], ":V1.*:Iq.*:[123]s", ">désemparer/.*:Q")))
def _g_cond_g2_289 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">laisser") and (g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|Ip.*:2[sp])", ">désemparer/.*:Q|:N") or (not g_morph(lToken[nTokenOffset], ":D") and g_morph(lToken[nLastToken-1+1], ":V1.*:Iq.*:[123]s", ">désemparer/.*:Q|:N")))
def _g_cond_g2_290 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">laisser") and (g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|Ip.*:2[sp])", ">désemparer/.*:Q") or (not g_morph(lToken[nTokenOffset], ":D") and g_morph(lToken[nLastToken-1+1], ":V1.*:Iq.*:[123]s", ">désemparer/.*:Q")))
def _g_cond_g2_291 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_analyse(lToken[nLastToken-1+1], ":V1.*:(?:Q|[123][sp])", ":[GM]")
def _g_cond_g2_292 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":", ":[GN]") and g_morph(lToken[nTokenOffset+2], ":V", ":M")
def _g_cond_g2_293 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":", ":[GN]") and g_morph(lToken[nLastToken-1+1], ":V", ":M|>(?:accompagner|armer|armurer|casquer|déguiser)/")
def _g_cond_g2_294 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":(?:Q|2p)", ":M") and not (lToken[nLastToken-1+1]["sValue"].endswith("ez") and g_value(lToken[nLastToken+1], "|vous|"))
def _g_cond_g2_295 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|[123][sp])")
def _g_cond_g2_296 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|[12][sp])", ":N")
def _g_cond_g2_297 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V1", ":M")
def _g_cond_g2_298 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|[123][sp])", ":[NM]")
def _g_cond_g2_299 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ">(?:passer|tenir)/") and g_morph(lToken[nLastToken-1+1], ":V1.*:(?:Q|[123][sp])", ":[NM]")
def _g_cond_g2_300 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V1.*:Y")
def _g_sugg_g2_149 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+2]["sValue"])
def _g_cond_g2_301 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:p", ":[NA].*:[si]")
def _g_cond_g2_302 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:s", ":[NA].*:[pi]")
def _g_cond_g2_303 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA]", ":(?:[123]p|P|X|G|V0)") and g_morph(lToken[nTokenOffset+3], ":[NA]", ":(?:G|[123][sp]|P|M)")
def _g_cond_g2_304 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N", ":A") and g_morph(lToken[nTokenOffset+2], ":A", ":N")
def _g_cond_g2_305 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA]", ":(?:[123]p|P|X|G|Y|V0)") and g_morph(lToken[nTokenOffset+3], ":[NA]", ":(?:G|[123][sp]|P|M)")
def _g_cond_g2_306 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":N", ":A") and g_morph(lToken[nTokenOffset+2], ":A")
def _g_cond_g2_307 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA]", ":(?:[123][sp]|P|X|G|Y|V0)|>air") and g_morph(lToken[nTokenOffset+3], ":[NA]", ":(?:G|[123][sp]|P|M)")
def _g_cond_g2_308 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA]", ":(?:G|[123][sp]|P|M)")
def _g_cond_g2_309 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|autres|")
def _g_cond_g2_310 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|en|")
def _g_cond_g2_311 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|j’|n’|tu|il|on|")
def _g_cond_g2_312 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":M") and g_morph(lToken[nTokenOffset+3], ":M") and g_morph(lToken[nTokenOffset+3], ":M")
def _g_cond_g2_313 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":M") and g_morph(lToken[nTokenOffset+4], ":M")
def _g_da_ppc2_1 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+2], ":Q")
def _g_cond_ppc2_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:[pi]") and g_morph(lToken[nTokenOffset+5], ":[NA].*:[si]")
def _g_cond_gv1_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|êtres|")
def _g_cond_gv1_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].endswith("e") and g_morph(lToken[nTokenOffset+2], ":V1.*:Ip.*:[13]s", ":[GMA]") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\belle +(?:ne +|n’|)$")
def _g_sugg_gv1_1 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+2]["sValue"], ":m:s")
def _g_cond_gv1_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and lToken[nTokenOffset+2]["sValue"].endswith("s") and g_morph(lToken[nTokenOffset+2], ":V1.*:Ip.*:2s", ":[GMA]") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\belles +(?:ne +|n’|)$")
def _g_sugg_gv1_2 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+2]["sValue"], ":m:p")
def _g_cond_gv1_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|avoirs|")
def _g_cond_gv1_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].endswith("e") and g_morph(lToken[nTokenOffset+2], ":V1.*:Ip.*:[13]s", ":[GM]|>envie/")
def _g_cond_gv1_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and lToken[nTokenOffset+2]["sValue"].endswith("s") and g_morph(lToken[nTokenOffset+2], ":V1.*:Ip.*:2s", ":[GM]")
def _g_cond_gv1_7 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]", ":G")
def _g_cond_gv1_8 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA]", ":G")
def _g_cond_gv1_9 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V[123]", ":(?:N|A|Q|W|G|3p)") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_")
def _g_cond_gv1_10 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V.*:3p", ":[GPY]") and not g_value(lToken[nLastToken+1], "|ils|elles|iel|iels|") and ( (g_morph(lToken[nTokenOffset+3], ":V...t_") and g_value(lToken[nLastToken+1], "le|la|l’|un|une|ce|cet|cette|mon|ton|son|ma|ta|sa|leur") and not g_tag(lToken[nLastToken+1], "_enum_")) or g_morph(lToken[nTokenOffset+3], ":V..i__") )
def _g_sugg_gv1_3 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":1p")
def _g_sugg_gv1_4 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+4]["sValue"], ":1p")
def _g_sugg_gv1_5 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+4]["sValue"], ":2p")
def _g_cond_gv1_11 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":V0")
def _g_cond_gv1_12 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":[123]p")
def _g_cond_gv1_13 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo
def _g_cond_gv1_14 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V[123]_.__p_e_", "*") or (g_value(lToken[nLastToken+1], "|<end>|") and not g_value(lToken[nTokenOffset], "|que|qu’|"))
def _g_sugg_gv1_6 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":m:s")
def _g_cond_gv1_15 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V[123]_.__p_e_", "*") or (g_value(lToken[nLastToken+1], "|<end>|") and not g_morph(lToken[nTokenOffset], ":R|>que/"))
def _g_sugg_gv1_7 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":f:s")
def _g_sugg_gv1_8 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":p")
def _g_sugg_gv1_9 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":m:p")
def _g_sugg_gv1_10 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":f:p")
def _g_cond_gv1_16 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":(?:Y|[123][sp])", ":[QAG]")
def _g_sugg_gv1_11 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_17 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nLastToken-2+1], ":[123]s") and g_morph(lToken[nLastToken-1+1], ":Q.*:p") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\bon (?:ne |)$")
def _g_sugg_gv1_12 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_18 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nLastToken-2+1], ">(?:matin|soir|soirée|nuit|après-midi|jour|année|semaine|mois|seconde|minute|heure|siècle|millénaire|fois)/")
def _g_sugg_gv1_13 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-4+1]["sValue"], ":m:s")
def _g_sugg_gv1_14 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+3]["sValue"])
def _g_sugg_gv1_15 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nTokenOffset+3]["sValue"])
def _g_cond_gv1_19 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not lToken[nTokenOffset+2]["sValue"].endswith("ons")
def _g_cond_gv1_20 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_21 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":(?:[123]s|P)") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_sugg_gv1_16 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_22 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":(?:[123]s|P)") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_23 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":(?:[123]s|P)") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_24 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+1], "_enum_") and g_morph(lToken[nTokenOffset+2], ":3s") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:et|ou)/") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_25 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+1], "_enum_") and g_morph(lToken[nTokenOffset+3], ":3s") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:et|ou)/") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_26 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+1], "_enum_") and g_morph(lToken[nTokenOffset+4], ":3s") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:et|ou)/") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_27 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "_enum_")
def _g_cond_gv1_28 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[RV]") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_29 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":(?:[123]s|P)") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_30 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R")
def _g_cond_gv1_31 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+1], "_enum_") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:et|ou)/") and g_morph(lToken[nTokenOffset+2], ":(?:[123]s|P)") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_sugg_gv1_17 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_32 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+1], "_enum_") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:et|ou)/") and g_morph(lToken[nTokenOffset+3], ":(?:[123]s|P)") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_33 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+1], "_enum_") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:et|ou)/") and g_morph(lToken[nTokenOffset+4], ":(?:[123]s|P)") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_34 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:ne|nous)/") and g_morph(lToken[nTokenOffset+2], ":1p") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_sugg_gv1_18 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_35 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:ne|nous)/") and g_morph(lToken[nTokenOffset+3], ":1p") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_36 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:ne|nous)/") and g_morph(lToken[nTokenOffset+4], ":1p") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_37 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_sugg_gv1_19 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_38 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[RV]") and g_morph(lToken[nTokenOffset+2], ":(?:3p|P)") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_39 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[RV]") and g_morph(lToken[nTokenOffset+3], ":(?:3p|P)") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_40 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[RV]") and g_morph(lToken[nTokenOffset+4], ":(?:3p|P)") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_41 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":(?:3p|P)") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_42 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":(?:3p|P)") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_43 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":(?:3p|P)") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not (g_tag(lToken[nTokenOffset], "_ceque_") and g_morph(lToken[nLastToken-1+1], ":3s"))
def _g_cond_gv1_44 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|")
def _g_sugg_gv1_20 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_45 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[123]s", ":[GNAQWY]")
def _g_sugg_gv1_21 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+3]["sValue"])
def _g_cond_gv1_46 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "[çcCÇ]’$|[cC][eE] n’$|[çÇ][aA] (?:[nN]’|)$") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)^ *ne pas ") and not g_morph(lToken[nTokenOffset], ":Y")
def _g_cond_gv1_47 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":Y", ":[AN]")
def _g_cond_gv1_48 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V1..t.*:Y", ":[AN]") and not g_morph(lToken[nLastToken+1], ":D")
def _g_cond_gv1_49 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+2], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_50 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+3], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_51 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+4], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_52 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+5], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_53 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_54 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_55 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_56 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":[123]s", ":(?:C|N.*:p)")
def _g_cond_gv1_57 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+2], ":[13]p")
def _g_cond_gv1_58 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+3], ":[13]p")
def _g_cond_gv1_59 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+4], ":[13]p")
def _g_cond_gv1_60 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") and not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and not g_morph(lToken[nTokenOffset+1], ":G") and g_morph(lToken[nTokenOffset+5], ":[13]p")
def _g_cond_gv1_61 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+2], ":[13]p")
def _g_cond_gv1_62 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+3], ":[13]p")
def _g_cond_gv1_63 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+4], ":[13]p")
def _g_cond_gv1_64 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+5], ":[13]p")
def _g_cond_gv1_65 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[me]", ":[GWf]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWMme]") and (g_morph(lToken[nTokenOffset+4], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+4], ":P")))
def _g_sugg_gv1_22 (lToken, nTokenOffset, nLastToken):
    return switchGender(lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_66 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[me]", ":[GWf]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWMme]") and (g_morph(lToken[nTokenOffset+5], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+5], ":P")))
def _g_cond_gv1_67 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[me]", ":[GWf]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWMme]") and (g_morph(lToken[nTokenOffset+6], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+6], ":P")))
def _g_cond_gv1_68 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[fe]", ":[GWm]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]") and (g_morph(lToken[nTokenOffset+4], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+4], ":P")))
def _g_cond_gv1_69 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[fe]", ":[GWm]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]") and (g_morph(lToken[nTokenOffset+5], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+5], ":P")))
def _g_cond_gv1_70 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and g_morph(lToken[nTokenOffset+3], ":[NA].*:[fe]", ":[GWm]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]") and (g_morph(lToken[nTokenOffset+6], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+6], ":P")))
def _g_cond_gv1_71 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and ((g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]")) or (g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and (g_morph(lToken[nTokenOffset+4], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+4], ":P")))
def _g_cond_gv1_72 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and ((g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]")) or (g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and (g_morph(lToken[nTokenOffset+5], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+5], ":P")))
def _g_cond_gv1_73 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and ((g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]")) or (g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and (g_morph(lToken[nTokenOffset+6], ":[123]s") or (not g_tag(lToken[nTokenOffset+3], "_enum_") and g_morph(lToken[nTokenOffset+6], ":P")))
def _g_cond_gv1_74 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and ((g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]")) or (g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and g_morph(lToken[nTokenOffset+4], ":(?:[123]p|P)")
def _g_cond_gv1_75 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and ((g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]")) or (g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and g_morph(lToken[nTokenOffset+5], ":(?:[123]p|P)")
def _g_cond_gv1_76 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|légion|néant|réalité|") and ((g_morph(lToken[nTokenOffset+3], ":[NA].*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWMfe]")) or (g_morph(lToken[nTokenOffset+3], ":[NA].*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and g_morph(lToken[nTokenOffset+6], ":(?:[123]p|P)")
def _g_cond_gv1_77 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return checkAgreement(lToken[nTokenOffset+5]["sValue"], lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_78 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return checkAgreement(lToken[nTokenOffset+6]["sValue"], lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_79 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "_enum_") and ((g_morph(lToken[nTokenOffset+2], ":M.*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWfe]")) or (g_morph(lToken[nTokenOffset+2], ":M.*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and (g_morph(lToken[nTokenOffset+3], ":[123]s") or (not g_tag(lToken[nTokenOffset+2], "_enum_") and g_morph(lToken[nTokenOffset+3], ":P")))
def _g_cond_gv1_80 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "_enum_") and ((g_morph(lToken[nTokenOffset+2], ":M.*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWfe]")) or (g_morph(lToken[nTokenOffset+2], ":M.*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and (g_morph(lToken[nTokenOffset+4], ":[123]s") or (not g_tag(lToken[nTokenOffset+2], "_enum_") and g_morph(lToken[nTokenOffset+4], ":P")))
def _g_cond_gv1_81 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "_enum_") and ((g_morph(lToken[nTokenOffset+2], ":M.*:f", ":[GWme]") and g_morph(lToken[nLastToken-1+1], ":A.*:m", ":[GWfe]")) or (g_morph(lToken[nTokenOffset+2], ":M.*:m", ":[GWfe]") and g_morph(lToken[nLastToken-1+1], ":A.*:f", ":[GWme]"))) and (g_morph(lToken[nTokenOffset+5], ":[123]s") or (not g_tag(lToken[nTokenOffset+2], "_enum_") and g_morph(lToken[nTokenOffset+5], ":P")))
def _g_cond_gv1_82 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return checkAgreement(lToken[nTokenOffset+4]["sValue"], lToken[nLastToken-1+1]["sValue"])
def _g_cond_gv1_83 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:[fp]", ":(?:G|:m:[si])") and g_morph(lToken[nTokenOffset+3], ":[123]s")
def _g_sugg_gv1_23 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_84 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:[mp]", ":(?:G|:f:[si])") and g_morph(lToken[nTokenOffset+3], ":[123]s")
def _g_sugg_gv1_24 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_85 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:[fs]", ":(?:G|:m:[pi])") and g_morph(lToken[nTokenOffset+3], ":[123]p")
def _g_sugg_gv1_25 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_86 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:[ms]", ":(?:G|:f:[pi])") and g_morph(lToken[nTokenOffset+3], ":[123]p")
def _g_sugg_gv1_26 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_87 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:m", ":[fe]") and g_morph(lToken[nLastToken-1+1], ":[NA]:f", ":[me]")
def _g_cond_gv1_88 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+2], ":A.*:f", ":[me]") and g_morph(lToken[nLastToken-1+1], ":[NA]:m", ":[fe]")
def _g_cond_gv1_89 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:p", ":[Gsi]") and g_morph(lToken[nTokenOffset+3], ":[123]s")
def _g_sugg_gv1_27 (lToken, nTokenOffset, nLastToken):
    return suggSing(lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_90 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+2], ":A.*:s", ":[Gpi]") and g_morph(lToken[nTokenOffset+3], ":[123]p")
def _g_sugg_gv1_28 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_91 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R|>(?:et|ou)/")
def _g_cond_gv1_92 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[me]", ":f")
def _g_cond_gv1_93 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:[fe]", ":m")
def _g_cond_gv1_94 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":M.*:m", ":M.*:[fe]")
def _g_cond_gv1_95 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NA].*:m:[pi]", ":[fe]") and g_morph(lToken[nLastToken-1+1], ":[NA].*:f")
def _g_cond_gv1_96 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+3], ":[NA].*:f:[pi]", ":[me]") and g_morph(lToken[nLastToken-1+1], ":[NA].*:(?:m:p|f:s)")
def _g_cond_gv1_97 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V0a.*:[123]s") and g_morph(lToken[nLastToken-1+1], ":A.*:p") and not g_value(lToken[nTokenOffset], "|on|")
def _g_cond_gv1_98 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+1], ":V0a.*:[123]p") and g_morph(lToken[nLastToken-1+1], ":A.*:s")
def _g_cond_gv1_99 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V0a")
def _g_cond_gv1_100 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:être|devenir|redevenir)/")
def _g_cond_gv1_101 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:sembler|rester|demeurer|para[îi]tre)/")
def _g_cond_gv1_102 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ":V0e.*:3s") and g_morph(lToken[nTokenOffset+2], ":(?:[123][sp]|A.*:[pf])", ":(?:G|W|Y|[me]:[si])")
def _g_cond_gv1_103 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morphVC(lToken[nTokenOffset+1], ":V0e.*:3p") and g_morph(lToken[nTokenOffset+2], ":(?:[123][sp]|A.*:[sf])", ":(?:G|W|Y|[me]:[pi])")
def _g_cond_gv1_104 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:être|devenir|redevenir)/") and not g_value(lToken[nTokenOffset], "|se|s’|")
def _g_sugg_gv1_29 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_105 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">(?:être|devenir|redevenir)/") and not g_value(lToken[nTokenOffset], "|nous|")
def _g_cond_gv1_106 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|rendez-vous|") and g_morphVC(lToken[nTokenOffset+1], ">(?:être|devenir|redevenir)/") and not g_value(lToken[nTokenOffset], "|vous|")
def _g_cond_gv1_107 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|rendez-vous|") and g_morphVC(lToken[nTokenOffset+1], ">(?:sembler|rester|demeurer|para[îi]tre)/")
def _g_cond_gv1_108 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo
def _g_sugg_gv1_30 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+3]["sValue"][:-1]
def _g_cond_gv1_109 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[RV]")
def _g_cond_gv1_110 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-2+1], ":[123]s")
def _g_cond_gv1_111 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-2+1], ":1p")
def _g_cond_gv1_112 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-2+1], ":3p")
def _g_cond_gv1_113 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[AQ].*:(?:[me]:p|f)", ":(?:G|Y|V0|P|[AQ].*:m:[is])") and not (g_morph(lToken[nTokenOffset+2], ":Y") and g_morph(lToken[nTokenOffset+3], ":3s"))
def _g_sugg_gv1_31 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+3]["sValue"])
def _g_cond_gv1_114 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[AQ].*:(?:[fe]:p|m)", ":(?:G|Y|V0|P|[AQ]:f:[is])") and not (g_morph(lToken[nTokenOffset+2], ":Y") and g_morph(lToken[nTokenOffset+2], ":3s"))
def _g_sugg_gv1_32 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+3]["sValue"])
def _g_cond_gv1_115 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[AQ].*:s", ":(?:G|Y|V0|P|[AQ].*:[ip])") and not (g_morph(lToken[nTokenOffset+2], ":Y") and g_morph(lToken[nTokenOffset+3], ":3s"))
def _g_cond_gv1_116 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[AQ].*:p", ":(?:G|Y|V0|P|[AQ].*:[is])") and not (g_morph(lToken[nTokenOffset+2], ":Y") and g_morph(lToken[nTokenOffset+3], ":3s"))
def _g_cond_gv1_117 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":3s") and g_morph(lToken[nTokenOffset+4], ":[AQ].*:[fp]", ":(?:G|Y|V0|P|[AQ].*:m:[si])")
def _g_sugg_gv1_33 (lToken, nTokenOffset, nLastToken):
    return suggMasSing(lToken[nTokenOffset+4]["sValue"])
def _g_cond_gv1_118 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":3s") and g_morph(lToken[nTokenOffset+4], ":[AQ].*:[mp]", ":(?:G|Y|V0|P|[AQ].*:f:[si])") and not g_morph(lToken[nTokenOffset], ":R")
def _g_sugg_gv1_34 (lToken, nTokenOffset, nLastToken):
    return suggFemSing(lToken[nTokenOffset+4]["sValue"])
def _g_cond_gv1_119 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":3p") and g_morph(lToken[nTokenOffset+4], ":[AQ].*:[fs]", ":(?:G|Y|V0|P|[AQ].*:m:[pi])")
def _g_sugg_gv1_35 (lToken, nTokenOffset, nLastToken):
    return suggMasPlur(lToken[nTokenOffset+4]["sValue"])
def _g_cond_gv1_120 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":3p") and g_morph(lToken[nTokenOffset+4], ":[AQ].*:[ms]", ":(?:G|Y|V0|P|[AQ].*:f:[pi])") and not g_morph(lToken[nTokenOffset], ":R")
def _g_sugg_gv1_36 (lToken, nTokenOffset, nLastToken):
    return suggFemPlur(lToken[nTokenOffset+4]["sValue"])
def _g_cond_gv1_121 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":3s") and g_morph(lToken[nTokenOffset+3], ":[AQ].*:p", ":(?:G|Y|V0|P|[AQ].*:[si])")
def _g_cond_gv1_122 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+2], ":3p") and g_morph(lToken[nTokenOffset+3], ":[AQ].*:s", ":(?:G|Y|V0|[AQ].*:[pi])")
def _g_cond_gv1_123 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return ( not g_morph(lToken[nTokenOffset+2], ":1p") or (g_morph(lToken[nTokenOffset+2], ":1p") and g_value(lToken[nTokenOffset], "|nous|ne|")) ) and g_morph(lToken[nTokenOffset+3], ":[AQ].*:s", ":(?:G|Y|V0|P|[AQ].*:[ip])") and not (g_morph(lToken[nTokenOffset+2], ":Y") and g_morph(lToken[nTokenOffset+3], ":3s"))
def _g_cond_gv1_124 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|barre|confiance|charge|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|")
def _g_cond_gv1_125 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|barre|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|") and (g_value(lToken[nTokenOffset], "|<start>|,|comme|comment|et|lorsque|lorsqu’|mais|où|ou|quand|qui|pourquoi|puisque|puisqu’|quoique|quoiqu’|si|s’|sinon|") or (g_value(lToken[nTokenOffset], "|que|qu’|") and g_morph(g_token(lToken, nTokenOffset+1-2), ":V|<start>", ":[NA]"))) and lToken[nLastToken-1+1]["sValue"].islower() and g_morph(lToken[nLastToken-1+1], ":(?:[123][sp]|Q.*:[fp])", ":(?:G|W|Q.*:m:[si])")
def _g_cond_gv1_126 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|barre|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|") and (g_value(lToken[nTokenOffset], "|<start>|,|comme|comment|et|lorsque|lorsqu’|mais|où|ou|quand|qui|pourquoi|puisque|puisqu’|quoique|quoiqu’|si|s’|sinon|") or (g_value(lToken[nTokenOffset], "|que|qu’|") and g_morph(g_token(lToken, nTokenOffset+1-2), ":V|<start>", ":[NA]"))) and lToken[nLastToken-1+1]["sValue"].islower() and g_morph(lToken[nLastToken-1+1], ":(?:[123][sp]|Q.*:[fp])", ":(?:G|W|N|Q.*:m:[si])")
def _g_cond_gv1_127 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|barre|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|") and (g_value(lToken[nTokenOffset], "|<start>|,|comme|comment|et|lorsque|lorsqu’|mais|où|ou|quand|qui|pourquoi|puisque|puisqu’|quoique|quoiqu’|si|s’|sinon|") or (g_value(lToken[nTokenOffset], "|que|qu’|") and g_morph(g_token(lToken, nTokenOffset+1-2), ":V|<start>", ":[NA]"))) and lToken[nLastToken-1+1]["sValue"].islower() and g_morph(lToken[nLastToken-1+1], ":(?:[123][sp])", ":[GWQ]")
def _g_cond_gv1_128 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":Os") and not g_value(lToken[nLastToken-1+1], "|barre|confiance|charge|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|") and (g_value(lToken[nTokenOffset], "|<start>|,|comme|comment|et|lorsque|lorsqu’|mais|où|ou|quand|qui|pourquoi|puisque|puisqu’|quoique|quoiqu’|si|s’|sinon|") or (g_value(lToken[nTokenOffset], "|que|qu’|") and g_morph(g_token(lToken, nTokenOffset+1-2), ":V|<start>", ":[NA]"))) and not lToken[nLastToken-1+1]["sValue"].isupper() and g_morph(lToken[nLastToken-1+1], ":(?:[123][sp]|Q.*:[fp])", ":(?:G|W|Q.*:m:[si])")
def _g_cond_gv1_129 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|barre|confiance|charge|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|") and (g_value(lToken[nTokenOffset], "|<start>|,|comme|comment|et|lorsque|lorsqu’|mais|où|ou|quand|qui|pourquoi|puisque|puisqu’|quoique|quoiqu’|si|s’|sinon|") or (g_value(lToken[nTokenOffset], "|que|qu’|") and g_morph(g_token(lToken, nTokenOffset+1-2), ":V|<start>", ":[NA]"))) and g_morph(lToken[nTokenOffset+2], ":[NA]", ":G") and not lToken[nLastToken-1+1]["sValue"].isupper() and g_morph(lToken[nLastToken-1+1], ":(?:[123][sp]|Y|Q.*:[fp])", ":(?:G|W|Q.*:m:[si])") and not (g_value(lToken[nLastToken-2+1], "|avions|") and g_morph(lToken[nLastToken-1+1], ":3[sp]"))
def _g_cond_gv1_130 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V0a")
def _g_cond_gv1_131 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":V0a", ":1p") and g_morph(lToken[nTokenOffset+3], ":V[0-3]..t_.*:Q.*:s", ":[GWpi]") and g_morph(lToken[nTokenOffset], ":(?:M|Os|N)", ":R") and not g_value(g_token(lToken, nTokenOffset+1-2), "|que|qu’|")
def _g_cond_gv1_132 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_") or g_morph(lToken[nTokenOffset+3], ":V[0-3]..t_")
def _g_cond_gv1_133 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken-1+1], "|confiance|charge|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|")
def _g_cond_gv1_134 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|A|avions|avoirs|") and g_morph(lToken[nTokenOffset+2], ":(?:Y|2p)")
def _g_cond_gv1_135 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and lToken[nTokenOffset+1]["sValue"] == "a" and lToken[nTokenOffset+2]["sValue"].endswith("r") and not g_value(lToken[nTokenOffset], "|n’|m’|t’|l’|il|on|elle|")
def _g_cond_gv1_136 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|A|avions|avoirs|") and g_morph(lToken[nTokenOffset+2], ":V(?:2.*:Ip.*:3s|3.*:Is.*:3s)", ":[NAQ]")
def _g_cond_gv1_137 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|A|avions|avoirs|") and g_morph(lToken[nTokenOffset+2], ":V3.*:Is.*:3s", ":[NAQ]")
def _g_cond_gv1_138 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA]") and not g_morph(lToken[nLastToken+1], ":(?:Y|Ov|D|LV)") and not ((g_value(lToken[nLastToken-1+1], "|décidé|essayé|tenté|oublié|imaginé|supplié|") and g_value(lToken[nLastToken+1], "|de|d’|")) or (g_value(lToken[nLastToken-1+1], "|réussi|pensé|") and g_value(lToken[nLastToken+1], "|à|")))
def _g_sugg_gv1_37 (lToken, nTokenOffset, nLastToken):
    return suggPlur(lToken[nLastToken-1+1]["sValue"], lToken[nTokenOffset+2]["sValue"])
def _g_cond_gv1_139 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:m")
def _g_cond_gv1_140 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NA].*:f", ">(?:fois|impression)/") and not g_morph(lToken[nLastToken+1], ":(?:Y|Ov|D|LV)|>qu[e’]/") and not ((g_value(lToken[nLastToken-1+1], "|décidé|essayé|tenté|oublié|imaginé|supplié|") and g_value(lToken[nLastToken+1], "|de|d’|")) or (g_value(lToken[nLastToken-1+1], "|réussi|pensé|") and g_value(lToken[nLastToken+1], "|à|")))
def _g_cond_gv1_141 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+3]["sValue"] != "pouvoir"
def _g_cond_gv1_142 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+2], ":V0a") and not g_value(lToken[nTokenOffset+3], "|barre|charge|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|")
def _g_cond_gv1_143 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":(?:Y|[123][sp])", ":[QMG]")
def _g_sugg_gv1_38 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+3]["sValue"], ":m:s")
def _g_cond_gv1_144 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and not g_value(lToken[nTokenOffset+1], "|les|l’|m’|t’|nous|vous|en|") and g_morph(lToken[nTokenOffset+3], ":Q.*:[fp]", ":m:[si]") and not g_morph(lToken[nTokenOffset+1], ":[NA].*:[fp]") and not look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\b(?:quel(?:le|)s?|combien) ")
def _g_cond_gv1_145 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nLastToken-2+1], ":V0a") and not g_value(lToken[nLastToken-1+1], "|barre|charge|confiance|cours|envie|peine|prise|crainte|cure|affaire|hâte|force|recours|")
def _g_cond_gv1_146 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":(?:Y|[123][sp])", ":[QMG]")
def _g_cond_gv1_147 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nLastToken-1+1], ":Q.*:[fp]", ":m:[si]")
def _g_cond_gv1_148 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+2], ":V0a") and g_morph(lToken[nTokenOffset+3], ":(?:Y|2p|Q.*:p|3[sp])", ":[GWsi]")
def _g_cond_gv1_149 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+2], ":V0a") and g_morph(lToken[nTokenOffset+3], ":(?:Y|2p|Q.*:s|3[sp])", ":[GWpi]")
def _g_sugg_gv1_39 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+3]["sValue"], ":p")
def _g_cond_gv1_150 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:p", ":[GEMWPsi]")
def _g_cond_gv1_151 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":A.*:[fp]", ":(?:G|E|M1|W|P|m:[si])") and not look(sSentence[lToken[nLastToken]["nEnd"]:], "^ +(?:y (?:a|aura|avait|eut)|d(?:ut|oit|evait|evra) y avoir|s’agi(?:ssait|t|ra))[, .]")
def _g_cond_gv1_152 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|bref|désolé|désolée|pire|") and g_morph(lToken[nTokenOffset+2], ":A.*:[mp]", ":(?:G|E|M1|W|P|f:[si])")
def _g_cond_gv1_153 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|bref|désolé|désolée|pire|") and g_morph(lToken[nTokenOffset+2], ":A.*:[fs]", ":(?:G|E|M1|W|P|m:[pi])")
def _g_cond_gv1_154 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+2], "|bref|désolé|désolée|pire|") and g_morph(lToken[nTokenOffset+2], ":A.*:[ms]", ":(?:G|E|M1|W|P|f:[pi])")
def _g_cond_gv1_155 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":(?:V1.*:[YQ]|Iq.*:[123]s)")
def _g_sugg_gv1_40 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+2]["sValue"], ":E", ":2p") + "-" + lToken[nTokenOffset+3]["sValue"]
def _g_cond_gv1_156 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":(?:V1.*:[YQ]|Iq.*:[123]s)") and g_morph(lToken[nTokenOffset+4], ":[ORC]", ":[NA]|>plupart/")
def _g_cond_gv1_157 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":(?:V1.*:[YQ]|Iq.*:[123]s)") and g_morph(lToken[nTokenOffset+4], ":[ORC]", ":[NA]")
def _g_cond_gv1_158 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":(?:V1.*:[YQ]|Iq.*:[123]s)") and g_morph(lToken[nTokenOffset+4], ":[ORCD]", ":Y")
def _g_cond_gv1_159 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not look(sSentence[lToken[nLastToken]["nEnd"]:], " soit ")
def _g_cond_gv1_160 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|je|")
def _g_cond_gv1_161 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[MYO]", ":A|>et/")
def _g_cond_gv1_162 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|tu|")
def _g_cond_gv1_163 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V[13].*:Ip.*:2s", ":G") and not g_value(lToken[nLastToken+1], "|tu|")
def _g_sugg_gv1_41 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"][:-1]
def _g_cond_gv1_164 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-1+1], ":V[13].*:Ip.*:2s", ":[GNAM]") and not g_value(lToken[nLastToken+1], "|tu|")
def _g_cond_gv1_165 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|il|elle|on|ils|elles|iel|iels|") and not (g_value(lToken[nLastToken-1+1], "|vient|dit|surgit|survient|provient|") and g_morph(lToken[nLastToken+1], ":(?:[MD]|Oo)|>[A-Z]/")) and g_morph(lToken[nLastToken-1+1], ":V[23].*:Ip.*:3s", ":G|>(?:devoir|suffire|para[îi]tre)/") and analyse(lToken[nLastToken-1+1]["sValue"][:-1]+"s", ":E:2s")
def _g_sugg_gv1_42 (lToken, nTokenOffset, nLastToken):
    return lToken[nLastToken-1+1]["sValue"][:-1]+"s"
def _g_cond_gv1_166 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|il|elle|on|ils|elles|iel|iels|") and not (g_value(lToken[nLastToken-1+1], "|vient|dit|surgit|survient|provient|") and g_morph(lToken[nLastToken+1], ":(?:[MD]|Oo)|>[A-Z]/")) and g_morph(lToken[nLastToken-1+1], ":V[23].*:Ip.*:3s", ":[GNA]|>(?:devoir|suffire|para[îi]tre)/") and analyse(lToken[nLastToken-1+1]["sValue"][:-1]+"s", ":E:2s")
def _g_cond_gv1_167 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|il|elle|on|") and not ( g_value(lToken[nLastToken-1+1], "|répond|") and (g_morph(lToken[nLastToken+1], ":[MD]|>[A-Z]/") or g_value(lToken[nLastToken+1], "|l’|d’|")) ) and g_morph(lToken[nLastToken-1+1], ":V3.*:Ip.*:3s", ":G")
def _g_cond_gv1_168 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|il|elle|on|") and not ( g_value(lToken[nLastToken-1+1], "|répond|") and (g_morph(lToken[nLastToken+1], ":[MD]|>[A-Z]/") or g_value(lToken[nLastToken+1], "|l’|d’|")) ) and g_morph(lToken[nLastToken-1+1], ":V3.*:Ip.*:3s", ":[GNA]")
def _g_cond_gv1_169 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E", ":[GM]|>(?:venir|aller|partir)/") and not g_value(lToken[nTokenOffset], "|de|d’|le|la|les|l’|je|j’|me|m’|te|t’|se|s’|nous|vous|lui|leur|")
def _g_cond_gv1_170 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V(?:1.*:Ip.*:2s|[23].*:Ip.*:3s)", ":[GM]|>(?:venir|aller|partir)/")
def _g_sugg_gv1_43 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+2]["sValue"], ":E", ":2s")+"-moi"
def _g_cond_gv1_171 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E:2s", ":[GM]|>(?:venir|aller|partir)/") and not g_value(lToken[nTokenOffset], "|de|d’|le|la|les|l’|me|m’|te|t’|se|s’|nous|vous|lui|leur|")
def _g_sugg_gv1_44 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+2]["sValue"], ":E", ":2s")+"-toi"
def _g_cond_gv1_172 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E", ":[GM]|>(?:venir|aller|partir)/") and g_morph(lToken[nLastToken+1], ":|<end>", ":(?:Y|3[sp]|Oo)|>(?:en|y)/") and g_morph(lToken[nTokenOffset], ":Cc|<start>|>,")
def _g_cond_gv1_173 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V(?:1.*:Ip.*:2s|[23].*:Ip.*:3s)", ":[GM]|>(?:venir|aller|partir)/") and not g_morph(lToken[nLastToken+1], ":Y")
def _g_sugg_gv1_45 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+2]["sValue"], ":E", ":2s")+"-"+lToken[nTokenOffset+3]["sValue"]
def _g_cond_gv1_174 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E", ":[GM]") and g_morph(lToken[nLastToken+1], ":|<end>", ":(?:Y|3[sp]|Oo)|>(?:en|y)/") and g_morph(lToken[nTokenOffset], ":Cc|<start>|>,")
def _g_cond_gv1_175 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E", ":[GM]|>(?:venir|aller|partir)") and g_morph(lToken[nLastToken+1], ":|<end>|>,", ":(?:N|A|Y|B|3[sp])|>(?:pour|plus|moins|mieux|peu|trop|très|en|y)/") and g_morph(lToken[nTokenOffset], ":Cc|<start>|>,")
def _g_cond_gv1_176 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V(?:1.*:Ip.*:2s|[23].*:Ip.*:3s)", ":[GM]|>(?:venir|aller|partir)/") and g_morph(lToken[nLastToken+1], ":|<end>|>,", ":(?:N|A|Y|B|3[sp])|>(?:pour|plus|moins|mieux|peu|trop|très|en|y)/")
def _g_sugg_gv1_46 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+2]["sValue"], ":E", ":2s")+"-les"
def _g_cond_gv1_177 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E", ":[GM]|>(?:venir|aller|partir)/") and g_morph(lToken[nLastToken+1], ":|<end>|>,", ":(?:N|A|Q|Y|MP|H|T)|>(?:pour|plus|moins|mieux|peu|plupart|trop|très|en|y|une?)/") and g_morph(lToken[nTokenOffset], ":Cc|<start>|>,")
def _g_cond_gv1_178 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V(?:1.*:Ip.*:2s|[23].*:Ip.*:3s)", ":[GM]|>(?:venir|aller|partir)/") and g_morph(lToken[nLastToken+1], ":|<end>|>,", ":(?:N|A|Y|B|T|MP|3[sp])|>(?:pour|plus|moins|mieux|peu|trop|très|une)/")
def _g_cond_gv1_179 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E", ":[GM]|>(?:aller|partir)/") and g_morph(lToken[nLastToken+1], ":|<end>|>,", ":(?:N|A|Q|Y|M|P|H|T|D|Ov)|>(?:pour|plus|moins|mieux|peu|plupart|trop|très|une?)/") and g_morph(lToken[nTokenOffset], ":Cc|<start>|>,")
def _g_cond_gv1_180 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V(?:1.*:Ip.*:2s|[23].*:Ip.*:3s)", ":[GM]|>(?:aller|partir)/") and g_morph(lToken[nLastToken+1], ":|<end>|>,", ":(?:N|A|Y|M|P|B|3[sp]|D|Ov)|>(?:pour|plus|moins|mieux|peu|trop|très|en|y)/")
def _g_cond_gv1_181 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+3], ":(?:Y|Ov)", ":[NAB]") and not g_morph(lToken[nTokenOffset], ":O[sv]")
def _g_sugg_gv1_47 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-3]+"’en"
def _g_cond_gv1_182 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nLastToken+1], "|guerre|")
def _g_cond_gv1_183 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset], "|va|") and g_value(lToken[nLastToken+1], "|guerre|"))
def _g_cond_gv1_184 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morph(lToken[nTokenOffset+1], ":E", ":[MG]") and g_morph(lToken[nLastToken+1], ":|<end>|>,", ":(?:Y|[123][sp])")
def _g_cond_gv1_185 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morphVC(lToken[nTokenOffset+1], ":E")
def _g_cond_gv1_186 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morphVC(lToken[nTokenOffset+1], ":E") and g_morph(lToken[nLastToken+1], ":[RC]|<end>|>,", ":Y")
def _g_cond_gv1_187 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and g_morphVC(lToken[nTokenOffset+1], ":E") and g_morph(lToken[nLastToken+1], ":[RC]|<end>|>,", ":[NAY]")
def _g_cond_gv1_188 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and not g_morph(lToken[nLastToken+1], ":Y")
def _g_cond_gv1_189 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and not g_value(lToken[nTokenOffset], "|tu|il|elle|on|ne|n’|") and not g_morph(lToken[nLastToken+1], ":Y")
def _g_cond_gv1_190 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 1) and not g_value(lToken[nLastToken+1], "|partie|")
def _g_cond_gv1_191 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[me]:[si]")
def _g_sugg_gv1_48 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[me]:[si]", True)
def _g_cond_gv1_192 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[fe]:[si]")
def _g_sugg_gv1_49 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[fe]:[si]", True)
def _g_cond_gv1_193 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[si]")
def _g_sugg_gv1_50 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[si]", True)
def _g_cond_gv1_194 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[pi]")
def _g_sugg_gv1_51 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[pi]", True)
def _g_cond_gv1_195 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[me]:[pi]")
def _g_sugg_gv1_52 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[me]:[pi]", True)
def _g_cond_gv1_196 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return hasSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[fe]:[pi]")
def _g_sugg_gv1_53 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nTokenOffset+3]["sValue"], ":[NA].*:[fe]:[pi]", True)
def _g_sugg_gv1_54 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":[NA].*:[me]:[si]", True)
def _g_sugg_gv1_55 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":[NA].*:[fe]:[si]", True)
def _g_sugg_gv1_56 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":[NA].*:[si]", True)
def _g_sugg_gv1_57 (lToken, nTokenOffset, nLastToken):
    return suggSimil(lToken[nLastToken-1+1]["sValue"], ":[NA].*:[pi]", True)
def _g_cond_gv1_197 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+1], "|rendez-vous|entre-nous|entre-vous|entre-elles|") and not g_morphVC(lToken[nTokenOffset+1], ":V0")
def _g_sugg_gv1_58 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nLastToken-1+1]["sValue"], ":s")
def _g_cond_gv1_198 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|l’|") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_que_")
def _g_cond_gv1_199 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "upron") and g_morph(lToken[nTokenOffset+1], ":V", ":Q|>soit/") and (g_morph(lToken[nTokenOffset+2], ":Y", ":[NAQ]") or lToken[nTokenOffset+2]["sValue"] in aSHOULDBEVERB) and not g_morph(lToken[nTokenOffset], ":Y|>ce/") and not g_value(lToken[nTokenOffset], "|c’|") and not g_value(g_token(lToken, nTokenOffset+1-2), "|ce|") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "suj_vinfi")
def _g_cond_gv1_200 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V", ":Q|>soit/") and g_morph(lToken[nTokenOffset+2], ":2p", ":[NAQ]")
def _g_cond_gv1_201 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V", ":Q|>soit/") and g_morph(lToken[nTokenOffset+2], ":V(?:2.*:Ip.*:3s|3.*:Is.*:3s)", ":[NAQ]") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "suj_vinfi")
def _g_cond_gv1_202 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V", ":Q|>soit/") and g_morph(lToken[nTokenOffset+2], ":V3.*:Is.*:3s", ":[NAQ]") and not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_") and not g_tag_before(lToken[nTokenOffset+1], dTags, "suj_vinfi")
def _g_cond_gv1_203 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+4]["sValue"].islower() and g_morph(lToken[nTokenOffset+3], ":[NA].*:m:[si]", ":G|>verbe/") and g_morph(lToken[nTokenOffset+4], ":V1.*:Y", ":M")
def _g_sugg_gv1_59 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+4]["sValue"], ":m:s")
def _g_cond_gv1_204 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+4]["sValue"].islower() and g_morph(lToken[nTokenOffset+3], ":[NA].*:f:[si]", ":G") and g_morph(lToken[nTokenOffset+4], ":V1.*:Y", ":M")
def _g_sugg_gv1_60 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+4]["sValue"], ":f:s")
def _g_cond_gv1_205 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+4]["sValue"].islower() and g_morph(lToken[nTokenOffset+3], ":[NA].*:e:[si]", ":G") and g_morph(lToken[nTokenOffset+4], ":V1.*:Y", ":M")
def _g_sugg_gv1_61 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+4]["sValue"], ":s")
def _g_cond_gv1_206 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+4]["sValue"].islower() and g_morph(lToken[nTokenOffset+3], ":[NA].*:[pi]", ":G") and g_morph(lToken[nTokenOffset+4], ":V1.*:Y", ":M")
def _g_sugg_gv1_62 (lToken, nTokenOffset, nLastToken):
    return suggVerbPpas(lToken[nTokenOffset+4]["sValue"], ":p")
def _g_cond_gv1_207 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[123][sp]")
def _g_sugg_gv1_63 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"].replace("ut", "ût").replace("UT", "ÛT")
def _g_cond_gv1_208 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower()
def _g_cond_gv1_209 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not (g_value(lToken[nTokenOffset+2], "|attendant|admettant|") and g_value(lToken[nLastToken+1], "|que|qu’|"))
def _g_cond_gv1_210 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not (g_morph(lToken[nTokenOffset], ":1p") and not g_value(lToken[nTokenOffset], "|sachons|veuillons|allons|venons|partons|") and g_value(g_token(lToken, nTokenOffset+1-2), "|<start>|,|"))
def _g_cond_gv1_211 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+2]["sValue"].islower() and not (g_morph(lToken[nTokenOffset], ":2p") and not g_value(lToken[nTokenOffset], "|sachez|veuillez|allez|venez|partez|") and g_value(g_token(lToken, nTokenOffset+1-2), "|<start>|,|"))
def _g_cond_gv1_212 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[123]s") or not g_morph(lToken[nTokenOffset+3], ":N.*:[me]:[si]")
def _g_cond_gv1_213 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[123]s") or not g_morph(lToken[nTokenOffset+3], ":N.*:[fe]:[si]")
def _g_cond_gv1_214 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[123]s") or not g_morph(lToken[nTokenOffset+3], ":N.*:[si]")
def _g_cond_gv1_215 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[123]s") or not g_morph(lToken[nTokenOffset+3], ":N.*:[pi]")
def _g_cond_gv1_216 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[123]s") or not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_gv1_217 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:[123]s|V0)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[me]:[si]")
def _g_cond_gv1_218 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:[123]s|V0)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[fe]:[si]")
def _g_cond_gv1_219 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:[123]s|V0)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[si]")
def _g_cond_gv1_220 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:[123]s|V0)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[pi]")
def _g_cond_gv1_221 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:[123]s|V0)") or not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_gv1_222 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3s|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[me]:[si]")
def _g_cond_gv1_223 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3s|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[fe]:[si]")
def _g_cond_gv1_224 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3s|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[si]")
def _g_cond_gv1_225 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3s|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[pi]")
def _g_cond_gv1_226 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3s|R)") or not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_gv1_227 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:1p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[me]:[si]")
def _g_cond_gv1_228 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:1p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[fe]:[si]")
def _g_cond_gv1_229 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:1p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[si]")
def _g_cond_gv1_230 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:1p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[pi]")
def _g_cond_gv1_231 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:1p|R)") or not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_gv1_232 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[me]:[si]")
def _g_cond_gv1_233 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[fe]:[si]")
def _g_cond_gv1_234 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[si]")
def _g_cond_gv1_235 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[pi]")
def _g_cond_gv1_236 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:2p|R)") or not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_gv1_237 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3p") or not g_morph(lToken[nTokenOffset+3], ":N.*:[me]:[si]")
def _g_cond_gv1_238 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3p") or not g_morph(lToken[nTokenOffset+3], ":N.*:[fe]:[si]")
def _g_cond_gv1_239 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3p") or not g_morph(lToken[nTokenOffset+3], ":N.*:[si]")
def _g_cond_gv1_240 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3p") or not g_morph(lToken[nTokenOffset+3], ":N.*:[pi]")
def _g_cond_gv1_241 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":3p") or not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_gv1_242 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[me]:[si]")
def _g_cond_gv1_243 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[fe]:[si]")
def _g_cond_gv1_244 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[si]")
def _g_cond_gv1_245 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3p|R)") or not g_morph(lToken[nTokenOffset+3], ":N.*:[pi]")
def _g_cond_gv1_246 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:3p|R)") or not g_morph(lToken[nTokenOffset+3], ":[NA]")
def _g_cond_gv1_247 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":(?:R|3s)")
def _g_cond_gv1_248 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+3], ":2s") or g_value(lToken[nTokenOffset], "|je|j’|tu|il|elle|on|nous|vous|ils|elles|iel|iels|")
def _g_cond_gv1_249 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":N", ":V")
def _g_cond_gv1_250 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NAM]") and g_morph(lToken[nTokenOffset+5], ":[NAM]") and g_morph(lToken[nTokenOffset+8], ":[NAM]")
def _g_cond_gv1_251 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NAM]") and g_morph(lToken[nTokenOffset+5], ":[NAM]") and g_morph(lToken[nTokenOffset+9], ":[NAM]")
def _g_cond_gv1_252 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[NAM]") and g_morph(lToken[nTokenOffset+5], ":[NAM]") and g_morph(lToken[nTokenOffset+10], ":[NAM]")
def _g_cond_gv1_253 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NAM]") and g_morph(lToken[nTokenOffset+6], ":[NAM]")
def _g_cond_gv1_254 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NAM]") and g_morph(lToken[nTokenOffset+7], ":[NAM]")
def _g_cond_gv1_255 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[NAM]") and g_morph(lToken[nTokenOffset+8], ":[NAM]")
def _g_cond_gv1_256 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V", ":N")
def _g_da_gv1_1 (lToken, nTokenOffset, nLastToken):
    return g_select(lToken[nTokenOffset+2], ":V")
def _g_cond_gv2_1 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nLastToken-1+1]["sValue"] != "A"
def _g_cond_gv2_2 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag_before(lToken[nTokenOffset+1], dTags, "_ceque_") and not g_value(lToken[nTokenOffset], "|tout|d’|l’|")
def _g_cond_gv2_3 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":[123][sp]", ":[NAGW]")
def _g_cond_gv2_4 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":(?:[123][sp]|P)") and g_morph(lToken[nTokenOffset+5], ":Q")
def _g_cond_gv2_5 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":(?:[123][sp]|P)") and g_morph(lToken[nTokenOffset+5], ":[QA]")
def _g_cond_gv2_6 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return (g_morph(lToken[nTokenOffset+2], ":M") and g_morph(lToken[nTokenOffset+4], ":M")) or (g_morph(lToken[nTokenOffset+2], ":Y") and g_morph(lToken[nTokenOffset+4], ":Y"))
def _g_cond_gv2_7 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[123][sp]") and g_morph(lToken[nTokenOffset+6], ":[123][sp]")
def _g_cond_gv2_8 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-2+1], ":[QA]")
def _g_cond_gv2_9 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken-2+1], ":Q")
def _g_cond_gv2_10 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":([123][sp]|P)")
def _g_cond_gv2_11 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":([123][sp]|P)") and g_morph(lToken[nTokenOffset+4], ":[QA]")
def _g_cond_gv2_12 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":([123][sp]|P)") and g_morph(lToken[nTokenOffset+4], ":Q")
def _g_cond_gv2_13 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1[sŝś]", ":[GW]")
def _g_sugg_gv2_1 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+2]["sValue"][:-1]+"é-je"
def _g_cond_gv2_14 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1[sŝś]", ":[GNW]") and not g_value(lToken[nTokenOffset+1], "|je|j’|il|elle|")
def _g_cond_gv2_15 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1s", ":[GW]")
def _g_cond_gv2_16 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1)
def _g_cond_gv2_17 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1s", ":[GNW]") and not g_value(lToken[nTokenOffset+1], "|je|j’|tu|")
def _g_cond_gv2_18 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:2s", ":[GW]")
def _g_cond_gv2_19 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:2s", ":[GNW]") and not g_value(lToken[nTokenOffset+1], "|je|j’|tu|")
def _g_cond_gv2_20 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:3s", ":[GW]")
def _g_cond_gv2_21 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:3s", ":[GNW]") and not g_value(lToken[nTokenOffset+1], "|ce|il|elle|on|")
def _g_cond_gv2_22 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:3s", ":[GNW]") and not g_value(lToken[nTokenOffset+1], "|ce|c’|ça|ç’|il|elle|on|iel|")
def _g_cond_gv2_23 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillons|sachons|")
def _g_cond_gv2_24 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:1p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillons|sachons|allons|venons|partons|")
def _g_cond_gv2_25 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and ( (g_value(lToken[nTokenOffset+2], "|avions|") and not g_morph(lToken[nTokenOffset+1], ":A.*:[me]:[sp]") and not g_morph(lToken[nLastToken-1+1], ":(:?3[sp]|Ov)")) or (g_morph(lToken[nTokenOffset+2], ":V.*:1p", ":[GNW]") and not g_morph(lToken[nTokenOffset+1], ":Os")) )
def _g_cond_gv2_26 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:2p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillez|sachez|")
def _g_cond_gv2_27 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:2p", ":[GW]") and not g_value(lToken[nTokenOffset+2], "|veuillez|sachez|allez|venez|partez|")
def _g_cond_gv2_28 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:2p", ":[GNW]") and not g_value(lToken[nTokenOffset+2], "|veuillez|") and not g_morph(lToken[nTokenOffset+1], ":Os")
def _g_cond_gv2_29 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:3p", ":[GW]")
def _g_cond_gv2_30 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 1, 1) and g_morph(lToken[nTokenOffset+2], ":V.*:3p", ":[GNW]") and not g_value(lToken[nTokenOffset+1], "|ce|ils|elles|iels|")
def _g_cond_gv2_31 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return lToken[nTokenOffset+3]["sValue"] == "est" or lToken[nTokenOffset+3]["sValue"] == "es"
def _g_cond_gv2_32 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo
def _g_sugg_gv2_2 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":1s")
def _g_sugg_gv2_3 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":2s")
def _g_cond_gv2_33 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R|>(?:et|ou)") and not (g_morph(lToken[nTokenOffset+2], ":Q") and g_morph(lToken[nTokenOffset], ":V0.*:3s"))
def _g_sugg_gv2_4 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+2]["sValue"], ":3s")
def _g_cond_gv2_34 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":3p")
def _g_cond_gv2_35 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R|>(?:et|ou)")
def _g_sugg_gv2_5 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3s")
def _g_cond_gv2_36 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+3], ":3p")
def _g_cond_gv2_37 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[VR]")
def _g_cond_gv2_38 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":[123]p")
def _g_sugg_gv2_6 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("e-", "es-").replace("E-", "ES-")
def _g_cond_gv2_39 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[123]p")
def _g_sugg_gv2_7 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":3s")
def _g_cond_gv2_40 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[VRD]")
def _g_cond_gv2_41 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":C|<start>|>,", ":(?:P|Q|[123][sp]|R)")
def _g_cond_gv2_42 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[CRV]|<start>|>,", ":D")
def _g_cond_gv2_43 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_tag(lToken[nTokenOffset+2], "neg") and g_morph(lToken[nTokenOffset], ":Cs|<start>|>,", ":(?:Y|P|Q|[123][sp]|R)") and not(g_morph(lToken[nTokenOffset+2], ":Y") and g_value(lToken[nTokenOffset], "|ne|"))
def _g_cond_gv2_44 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":[CRV]|<start>|>,")
def _g_cond_gv2_45 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":Cs|<start>|>,", ":(?:Y|P|Q|[123][sp]|R)")
def _g_cond_gv2_46 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":(?:Cs|R|V)|<start>|>,")
def _g_cond_gv2_47 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_value(lToken[nTokenOffset+2], "|avoir|croire|être|devenir|redevenir|voir|sembler|paraître|paraitre|sentir|rester|retrouver|") and g_morph(lToken[nTokenOffset+3], ":[NA]"))
def _g_cond_gv2_48 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "_enum_") and g_morph(lToken[nTokenOffset], ":C|<start>|>,", ":[YP]") and g_morph(lToken[nTokenOffset+2], ":[NA].*:[si]", ":G") and not ( (g_value(lToken[nTokenOffset+2], "|dizaine|douzaine|quinzaine|vingtaine|trentaine|quarantaine|cinquantaine|soixantaine|centaine|majorité|minorité|millier|partie|poignée|tas|paquet|moitié|") or g_tag_before(lToken[nTokenOffset+1], dTags, "_ni_") or g_value(lToken[nTokenOffset], "|et|ou|")) and g_morph(lToken[nTokenOffset+3], ":3?p") )
def _g_cond_gv2_49 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not checkAgreement(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_gv2_50 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and isVeryAmbiguousAndWrong(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"], ":s", ":3s", g_value(lToken[nTokenOffset], "|<start>|,|"))
def _g_sugg_gv2_8 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3s", suggSing)
def _g_cond_gv2_51 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "_enum_") and g_morph(lToken[nTokenOffset], ":C|<start>|>,", ":[YP]") and g_morph(lToken[nTokenOffset+2], ":[NA].*:[si]", ":G") and not ( (g_value(lToken[nTokenOffset+2], "|dizaine|douzaine|quinzaine|vingtaine|trentaine|quarantaine|cinquantaine|soixantaine|centaine|majorité|minorité|millier|partie|poignée|tas|paquet|moitié|") or g_tag_before(lToken[nTokenOffset+1], dTags, "_ni_") or g_value(lToken[nTokenOffset], "|et|ou|")) and g_morph(lToken[nTokenOffset+4], ":3p") )
def _g_sugg_gv2_9 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+4]["sValue"], ":3s")
def _g_cond_gv2_52 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":C|<start>|>(?:,|dont)", ":(?:Y|P|Q|[123][sp]|R)̉|>(?:sauf|excepté|et|ou)/")
def _g_cond_gv2_53 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], "<start>|>(?:,|dont)/|:R")
def _g_cond_gv2_54 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":C|<start>|>,", ":(?:Y|P|Q|[123][sp]|R)")
def _g_cond_gv2_55 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not (g_morph(lToken[nTokenOffset], ":R") and g_morph(lToken[nLastToken-1+1], ":3p"))
def _g_cond_gv2_56 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":R") and not (g_morph(lToken[nTokenOffset+2], ":Q") and g_morph(lToken[nTokenOffset], ":V0.*:3p"))
def _g_sugg_gv2_10 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+2]["sValue"], ":3p")
def _g_cond_gv2_57 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":3s")
def _g_sugg_gv2_11 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3p")
def _g_cond_gv2_58 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+3], ":3s")
def _g_cond_gv2_59 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[123]s")
def _g_cond_gv2_60 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo and g_morph(lToken[nTokenOffset+2], ":[123]s")
def _g_sugg_gv2_12 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"].replace("s", "").replace("S", "")
def _g_cond_gv2_61 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_tag(lToken[nTokenOffset+1], "bcp_plur") and not g_morph(lToken[nTokenOffset+2], ":3p")
def _g_cond_gv2_62 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_tag(lToken[nTokenOffset+1], "bcp_sing") and not g_morph(lToken[nTokenOffset+2], ":3s")
def _g_cond_gv2_63 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and lToken[nTokenOffset+2]["sValue"] != "a" and not g_tag(lToken[nTokenOffset+1], "bcp_sing") and not g_morph(lToken[nTokenOffset+2], ":3p") and not (g_space_between_tokens(lToken[nTokenOffset+1], lToken[nTokenOffset+1+1], 1, 2) and g_morph(lToken[nTokenOffset+2], ":V0"))
def _g_sugg_gv2_13 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nLastToken-1+1]["sValue"], ":3p")
def _g_cond_gv2_64 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":[12]p")
def _g_cond_gv2_65 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[VR]|>(?:et|ou)/")
def _g_cond_gv2_66 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":Cs|<start>|>,") and not( g_morph(lToken[nTokenOffset+3], ":3s") and look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\b(?:l[ea] |l’|une? |ce(?:tte|t|) |[mts](?:on|a) |[nv]otre ).+ entre .+ et ") )
def _g_cond_gv2_67 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and isAmbiguousAndWrong(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"], ":p", ":3p")
def _g_sugg_gv2_14 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3p", suggPlur)
def _g_cond_gv2_68 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":Cs|<start>|>,") and not( g_morph(lToken[nTokenOffset+4], ":3s") and look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\b(?:l[ea] |l’|une? |ce(?:tte|t|) |[mts](?:on|a) |[nv]otre ).+ entre .+ et ") )
def _g_sugg_gv2_15 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+4]["sValue"], ":3p")
def _g_cond_gv2_69 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and isVeryAmbiguousAndWrong(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"], ":p", ":3p", g_value(lToken[nTokenOffset], "|<start>|,|"))
def _g_cond_gv2_70 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and isVeryAmbiguousAndWrong(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"], ":m:p", ":3p", g_value(lToken[nTokenOffset], "|<start>|,|"))
def _g_sugg_gv2_16 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3p", suggMasPlur)
def _g_cond_gv2_71 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and isVeryAmbiguousAndWrong(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"], ":f:p", ":3p", g_value(lToken[nTokenOffset], "|<start>|,|"))
def _g_sugg_gv2_17 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+3]["sValue"], ":3p", suggFemPlur)
def _g_cond_gv2_72 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":Cs|<start>|>,") and not( g_morph(lToken[nTokenOffset+3], ":3s") and look(sSentence[:lToken[1+nTokenOffset]["nStart"]], "(?i)\\b(?:l[ea] |l’|une? |ce(?:tte|t|) |[mts](?:on|a) |[nv]otre ).+ entre .+ et ") ) and not checkAgreement(lToken[nTokenOffset+2]["sValue"], lToken[nTokenOffset+3]["sValue"])
def _g_cond_gv2_73 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nLastToken+1], ":(?:R|D.*:p)|>au/|<end>|>,")
def _g_cond_gv2_74 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+4], ":[NA]")
def _g_cond_gv2_75 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and not checkAgreement(lToken[nTokenOffset+3]["sValue"], lToken[nTokenOffset+4]["sValue"])
def _g_sugg_gv2_18 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+4]["sValue"], ":3p", suggPlur)
def _g_sugg_gv2_19 (lToken, nTokenOffset, nLastToken):
    return suggVerb(lToken[nTokenOffset+5]["sValue"], ":3p")
def _g_cond_gv2_76 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+2], "_enum_") and g_morph(lToken[nTokenOffset+2], ":M")
def _g_cond_gv2_77 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":M") and g_morph(lToken[nTokenOffset+3], ":M") and not g_morph(lToken[nTokenOffset], ":[RV]|>(?:des?|du|et|ou|ni)/")
def _g_cond_gv2_78 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset], ":[RV]")
def _g_cond_gv2_79 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+4], "|plupart|majorité|groupe|") and not g_tag(lToken[nTokenOffset+4], "_enum_") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":D"))
def _g_cond_gv2_80 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset+4], "|plupart|majorité|groupe|") and not g_tag(lToken[nTokenOffset+4], "_enum_") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":D")) and not (g_morph(lToken[nTokenOffset+4], ":Y") and g_morph(lToken[nTokenOffset+2], ">(?:pouvoir|vouloir|devoir)"))
def _g_cond_gv2_81 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":R") and not g_value(lToken[nTokenOffset+4], "|plupart|majorité|groupe|") and not (g_value(lToken[nLastToken+1], "|et|ou|") and g_morph(g_token(lToken, nLastToken+2), ":D"))
def _g_cond_gv2_82 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset], ":R")
def _g_cond_gv2_83 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V0e", ":3s")
def _g_cond_gv2_84 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not ( g_morph(lToken[nTokenOffset+3], ":3p") and (g_value(lToken[nLastToken+1], "|et|") or g_tag(lToken[nTokenOffset+5], "_enum_")) )
def _g_cond_gv2_85 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return bCondMemo
def _g_sugg_gv2_20 (lToken, nTokenOffset, nLastToken):
    return lToken[nTokenOffset+1]["sValue"][:-1]
def _g_cond_gv2_86 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+3], ":V0e", ":3p")
def _g_cond_gv2_87 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+2], ":[12]s") and not g_value(lToken[nLastToken+1], "|je|tu|")
def _g_cond_gv2_88 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not bCondMemo and g_morph(lToken[nTokenOffset+2], ":[12]p") and not g_value(lToken[nLastToken+1], "|nous|vous|")
def _g_cond_gv2_89 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morphVC(lToken[nTokenOffset+1], ">avoir/")
def _g_cond_gv2_90 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+4], ":K")
def _g_sugg_gv2_21 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+4]["sValue"], ":Iq", ":1s")
def _g_sugg_gv2_22 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+4]["sValue"], ":Iq", ":2s")
def _g_sugg_gv2_23 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+4]["sValue"], ":Iq", ":3s")
def _g_sugg_gv2_24 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+4]["sValue"], ":Iq", ":1p")
def _g_sugg_gv2_25 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+4]["sValue"], ":Iq", ":2p")
def _g_sugg_gv2_26 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+4]["sValue"], ":Iq", ":3p")
def _g_cond_gv2_91 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":K")
def _g_sugg_gv2_27 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+5]["sValue"], ":Iq", ":3s")
def _g_sugg_gv2_28 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+5]["sValue"], ":Iq", ":3p")
def _g_sugg_gv2_29 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+4]["sValue"], ":I", lToken[nTokenOffset+3]["sValue"])
def _g_cond_gv2_92 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+1], ":V")
def _g_sugg_gv2_30 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nLastToken-1+1]["sValue"], ":S", lToken[nLastToken-2+1]["sValue"])
def _g_cond_gv2_93 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_morph(lToken[nTokenOffset+1], ":Q")
def _g_cond_gv2_94 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_tag(lToken[nTokenOffset+1], "upron")
def _g_cond_gv2_95 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_value(lToken[nTokenOffset], "|la|")
def _g_cond_gv2_96 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return not g_tag(lToken[nTokenOffset+1], "upron") and not g_tag(lToken[nTokenOffset+1], "neg") and g_morph(lToken[nTokenOffset+1], ":V", ":N")
def _g_cond_gv2_97 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_tag(lToken[nTokenOffset+2], "upron")
def _g_sugg_gv2_31 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+3]["sValue"], ":S", lToken[nTokenOffset+2]["sValue"])
def _g_sugg_gv2_32 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+4]["sValue"], ":S", lToken[nTokenOffset+3]["sValue"])
def _g_sugg_gv2_33 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+5]["sValue"], ":S", lToken[nTokenOffset+4]["sValue"])
def _g_sugg_gv2_34 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+6]["sValue"], ":S", lToken[nTokenOffset+5]["sValue"])
def _g_cond_gv2_98 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_morph(lToken[nTokenOffset+5], ":I", ":S")
def _g_sugg_gv2_35 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+3]["sValue"], ":I", lToken[nTokenOffset+2]["sValue"])
def _g_sugg_gv2_36 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+3]["sValue"], ":I", "je")
def _g_sugg_gv2_37 (lToken, nTokenOffset, nLastToken):
    return suggVerbMode(lToken[nTokenOffset+5]["sValue"], ":I", lToken[nTokenOffset+4]["sValue"])
def _g_cond_gv2_99 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 0, 0)
def _g_sugg_gv2_38 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+4]["sValue"], ":E", ":2s")
def _g_cond_gv2_100 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+2], lToken[nTokenOffset+2+1], 0, 0) and g_morph(lToken[nTokenOffset+4], ">(?:être|devenir|redevenir|sembler|para[iî]tre)/")
def _g_cond_gv2_101 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+3], lToken[nTokenOffset+3+1], 0, 0)
def _g_sugg_gv2_39 (lToken, nTokenOffset, nLastToken):
    return suggVerbTense(lToken[nTokenOffset+5]["sValue"], ":E", ":2s")
def _g_cond_gv2_102 (lToken, nTokenOffset, nLastToken, sCountry, bCondMemo, dTags, sSentence, sSentence0):
    return g_space_between_tokens(lToken[nTokenOffset+3], lToken[nTokenOffset+3+1], 0, 0) and g_morph(lToken[nTokenOffset+5], ">(?:être|devenir|redevenir|sembler|para[iî]tre)/")

