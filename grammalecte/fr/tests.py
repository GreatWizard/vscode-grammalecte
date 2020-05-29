#! python3

"""
Grammar checker tests for French language
"""

import unittest
import os
import re
import time
from contextlib import contextmanager

from ..graphspell.ibdawg import IBDAWG
from ..graphspell.echo import echo
from . import gc_engine as gce
from . import conj
from . import phonet
from . import mfsp


@contextmanager
def timeblock (label, hDst):
    "performance counter (contextmanager)"
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        print('{} : {}'.format(label, end - start))
        if hDst:
            hDst.write("{:<12.6}".format(end-start))


def perf (sVersion, hDst=None):
    "performance tests"
    print("\nPerformance tests")
    gce.load()
    gce.parse("Texte sans importance… utile pour la compilation des règles avant le calcul des perfs.")

    spHere, _ = os.path.split(__file__)
    with open(os.path.join(spHere, "perf.txt"), "r", encoding="utf-8") as hSrc:
        if hDst:
            hDst.write("{:<12}{:<20}".format(sVersion, time.strftime("%Y.%m.%d %H:%M")))
        for sText in ( s.strip() for s in hSrc if not s.startswith("#") and s.strip() ):
            with timeblock(sText[:sText.find(".")], hDst):
                gce.parse(sText)
        if hDst:
            hDst.write("\n")


def _fuckBackslashUTF8 (s):
    "fuck that shit"
    return s.replace("\u2019", "'").replace("\u2013", "–").replace("\u2014", "—")


class TestDictionary (unittest.TestCase):
    "Test du correcteur orthographique"

    @classmethod
    def setUpClass (cls):
        cls.oDic = IBDAWG("fr-allvars.bdic")

    def test_lookup (self):
        for sWord in ["branche", "Émilie"]:
            self.assertTrue(self.oDic.lookup(sWord), sWord)

    def test_lookup_failed (self):
        for sWord in ["Branche", "BRANCHE", "BranchE", "BRanche", "BRAnCHE", "émilie"]:
            self.assertFalse(self.oDic.lookup(sWord), sWord)

    def test_isvalid (self):
        for sWord in ["Branche", "branche", "BRANCHE", "Émilie", "ÉMILIE", "aujourd'hui", "aujourd’hui", "Aujourd'hui", "Aujourd’hui"]:
            self.assertTrue(self.oDic.isValid(sWord), sWord)

    def test_isvalid_failed (self):
        for sWord in ["BranchE", "BRanche", "BRAnCHE", "émilie", "éMILIE", "émiLie"]:
            self.assertFalse(self.oDic.isValid(sWord), sWord)


class TestConjugation (unittest.TestCase):
    "Tests des conjugaisons"

    @classmethod
    def setUpClass (cls):
        pass

    def test_isverb (self):
        for sVerb in ["avoir", "être", "aller", "manger", "courir", "venir", "faire", "finir"]:
            self.assertTrue(conj.isVerb(sVerb), sVerb)
        for sVerb in ["berk", "a", "va", "contre", "super", "", "à"]:
            self.assertFalse(conj.isVerb(sVerb), sVerb)

    def test_hasconj (self):
        for sVerb, sTense, sWho in [("aller", ":E", ":2s"), ("avoir", ":Is", ":1s"), ("être", ":Ip", ":2p"),
                                    ("manger", ":Sp", ":3s"), ("finir", ":K", ":3p"), ("prendre", ":If", ":1p")]:
            self.assertTrue(conj.hasConj(sVerb, sTense, sWho), sVerb)

    def test_getconj (self):
        for sVerb, sTense, sWho, sConj in [("aller", ":E", ":2s", "va"), ("avoir", ":Iq", ":1s", "avais"), ("être", ":Ip", ":2p", "êtes"),
                                           ("manger", ":Sp", ":3s", "mange"), ("finir", ":K", ":3p", "finiraient"), ("prendre", ":If", ":1p", "prendrons")]:
            self.assertEqual(conj.getConj(sVerb, sTense, sWho), sConj, sVerb)


class TestPhonet (unittest.TestCase):
    "Tests des équivalences phonétiques"

    @classmethod
    def setUpClass (cls):
        cls.lSet = [
            ["ce", "se"],
            ["ces", "ses", "sais", "sait"],
            ["cet", "cette", "sept", "set", "sets"],
            ["dé", "dés", "dès", "dais", "des"],
            ["don", "dons", "dont"],
            ["été", "étaie", "étaies", "étais", "était", "étai", "étés", "étaient"],
            ["faire", "fer", "fers", "ferre", "ferres", "ferrent"],
            ["fois", "foi", "foie", "foies"],
            ["la", "là", "las"],
            ["mes", "mets", "met", "mai", "mais"],
            ["mon", "mont", "monts"],
            ["mot", "mots", "maux"],
            ["moi", "mois"],
            ["notre", "nôtre", "nôtres"],
            ["or", "ors", "hors"],
            ["hou", "houe", "houes", "ou", "où", "houx"],
            ["peu", "peux", "peut"],
            ["ses", "ces", "sais", "sait"],
            ["son", "sons", "sont"],
            ["tes", "tais", "tait", "taie", "taies", "thé", "thés"],
            ["toi", "toit", "toits"],
            ["ton", "tons", "thon", "thons", "tond", "tonds"],
            ["voir", "voire"]
        ]

    def test_getsimil (self):
        for aSet in self.lSet:
            for sWord in aSet:
                self.assertListEqual(phonet.getSimil(sWord), sorted(aSet))


class TestMasFemSingPlur (unittest.TestCase):
    "Tests des masculins, féminins, singuliers et pluriels"

    @classmethod
    def setUpClass (cls):
        cls.lPlural = [
            ("travail", ["travaux"]),
            ("vœu", ["vœux"]),
            ("gentleman", ["gentlemans", "gentlemen"])
        ]

    def test_getplural (self):
        for sSing, lPlur in self.lPlural:
            self.assertListEqual(mfsp.getMiscPlural(sSing), lPlur)


class TestGrammarChecking (unittest.TestCase):
    "Tests du correcteur grammatical"

    @classmethod
    def setUpClass (cls):
        gce.load()
        cls._zError = re.compile(r"\{\{.*?\}\}")
        cls._aTestedRules = set()

    def test_parse (self):
        zOption = re.compile("^__([a-zA-Z0-9]+)__ ")
        spHere, _ = os.path.split(__file__)
        with open(os.path.join(spHere, "gc_test.txt"), "r", encoding="utf-8") as hSrc:
            nError = 0
            for sLine in ( s for s in hSrc if not s.startswith("#") and s.strip() ):
                sLineNum = sLine[:10].strip()
                sLine = sLine[10:].strip()
                sOption = None
                m = zOption.search(sLine)
                if m:
                    sLine = sLine[m.end():]
                    sOption = m.group(1)
                if "->>" in sLine:
                    sErrorText, sExceptedSuggs = self._splitTestLine(sLine)
                    if sExceptedSuggs.startswith('"') and sExceptedSuggs.endswith('"'):
                        sExceptedSuggs = sExceptedSuggs[1:-1]
                else:
                    sErrorText = sLine.strip()
                    sExceptedSuggs = ""
                sExpectedErrors = self._getExpectedErrors(sErrorText)
                sTextToCheck = sErrorText.replace("}}", "").replace("{{", "")
                sFoundErrors, sListErr, sFoundSuggs = self._getFoundErrors(sTextToCheck, sOption)
                # tests
                if sExpectedErrors != sFoundErrors:
                    print("\n# Line num: " + sLineNum + \
                          "\n> to check: " + _fuckBackslashUTF8(sTextToCheck) + \
                          "\n  expected: " + sExpectedErrors + \
                          "\n  found:    " + sFoundErrors + \
                          "\n  errors:   \n" + sListErr)
                    nError += 1
                elif sExceptedSuggs:
                    if sExceptedSuggs != sFoundSuggs:
                        print("\n# Line num: " + sLineNum + \
                              "\n> to check: " + _fuckBackslashUTF8(sTextToCheck) + \
                              "\n  expected: " + sExceptedSuggs + \
                              "\n  found:    " + sFoundSuggs + \
                              "\n  errors:   \n" + sListErr)
                        nError += 1
            if nError:
                print("Unexpected errors:", nError)
        # untested rules
        i = 0
        echo("Untested rules:")
        for _, sOpt, sLineId, sRuleId in gce.listRules():
            if sOpt != "@@@@" and sRuleId not in self._aTestedRules and not re.search("^[0-9]+[sp]$|^[pd]_", sRuleId):
                echo(sLineId + "/" + sRuleId)
                i += 1
        echo("[{} untested rules]".format(i))

    def _splitTestLine (self, sLine):
        sText, sSugg = sLine.split("->>")
        return (sText.strip(), sSugg.strip())

    def _getFoundErrors (self, sLine, sOption):
        if sOption:
            gce.setOption(sOption, True)
            aErrs = gce.parse(sLine)
            gce.setOption(sOption, False)
        else:
            aErrs = gce.parse(sLine)
        sRes = " " * len(sLine)
        sListErr = ""
        lAllSugg = []
        for dErr in aErrs:
            sRes = sRes[:dErr["nStart"]] + "~" * (dErr["nEnd"] - dErr["nStart"]) + sRes[dErr["nEnd"]:]
            sListErr += "    * {sLineId} / {sRuleId}  at  {nStart}:{nEnd}\n".format(**dErr)
            lAllSugg.append("|".join(dErr["aSuggestions"]))
            self._aTestedRules.add(dErr["sRuleId"])
            # test messages
            if "<start>" in dErr["sMessage"] or "<end>" in dErr["sMessage"]:
                print("\n# Line num : " + dErr["sLineId"] + \
                      "\n  rule name: " + dErr["sRuleId"] + \
                      "\n  message  : " + dErr["sMessage"])
        return sRes, sListErr, "|||".join(lAllSugg)

    def _getExpectedErrors (self, sLine):
        sRes = " " * len(sLine)
        for i, m in enumerate(self._zError.finditer(sLine)):
            nStart = m.start() - (4 * i)
            nEnd = m.end() - (4 * (i+1))
            sRes = sRes[:nStart] + "~" * (nEnd - nStart) + sRes[nEnd:-4]
        return sRes


def main():
    "start function"
    unittest.main()


if __name__ == '__main__':
    main()
