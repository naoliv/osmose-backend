#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Frederic Rodrigo 2014                                      ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

from plugins.Plugin import Plugin
from modules.downloader import urlread
import re


class TagFix_Postcode(Plugin):

    def parse_format(self, reline, format):
        if format[-1] == ')':
            format = map(lambda x: x.strip(), format[:-1].split('('))
        else:
            format = [format]

        regexs = []
        for f in format:
            if reline.match(f):
                regex = f.replace("N", "[0-9]").replace("A", "[A-Z]").replace("CC", "(:?"+self.Country+")?")
                regexs.append(regex)
                regexs.append(regex.replace(" ",""))

        if len(regexs) > 1:
            return "^(("+(")|(".join(regexs))+"))$"
        elif len(regexs) == 1:
            return "^"+regexs[0]+"$"

    def list_postcode(self):
        reline = re.compile("^[-CAN ]+$")
        # remline = re.compile("^[-CAN ]+ *\([-CAN ]+\)$")
        data = urlread("http://en.wikipedia.org/wiki/List_of_postal_codes?action=raw", 1)
        data = filter(lambda t: len(t)>2 and t[1] != "- no codes -", map(lambda x: map(lambda y: y.strip(), x.split("|"))[5:8], data.split("|-")[1:-1]))
        postcode = {}
        for line in data:
            iso = line[0][0:2]
            format_area = line[1]
            format_street = line[2]
            # note = line[3]

            postcode[iso] = {}
            if format_area != '':
                postcode[iso]['area'] = self.parse_format(reline, format_area)
            if format_street != '':
                postcode[iso]['street'] = self.parse_format(reline, format_street)

        return postcode

    def init(self, logger):
        Plugin.init(self, logger)
        self.errors[31901] = {"item": 3190, "level": 3, "tag": ["postcode", "fix:chair"], "desc": T_(u"Invalid postcode") }

        self.Country = self.father.config.options.get("country")
        self.CountryPostcodeArea = None
        self.CountryPostcodeStreet = None
        if not self.Country:
            return
        postcode = self.list_postcode()
        if self.Country in postcode:
            if 'area' in postcode[self.Country] and postcode[self.Country]['area'] is not None:
                self.CountryPostcodeArea = re.compile(postcode[self.Country]['area'])
            if 'street' in postcode[self.Country] and postcode[self.Country]['street'] is not None:
                self.CountryPostcodeStreet = re.compile(postcode[self.Country]['street'])
            elif 'area' in postcode[self.Country] and postcode[self.Country]['area'] is not None:
                self.CountryPostcodeStreet = self.CountryPostcodeArea

    def node(self, data, tags):
        err = []
        if self.CountryPostcodeArea and 'postal_code' in tags and not self.CountryPostcodeArea.match(tags['postal_code']):
            err.append((31901, 1, {"en": "Invalid area postcode %s for country code %s" % (tags['postal_code'], self.Country), "fr": "Code postal de zone %s invalide pour le code pays %s" % (tags['postal_code'], self.Country)}))
        if self.CountryPostcodeStreet and 'addr:postcode' in tags and not self.CountryPostcodeStreet.match(tags['addr:postcode']):
            err.append((31901, 2, {"en": "Invalid street level postcode %s for country code %s" % (tags['addr:postcode'], self.Country), "fr": "Code postal de niveau rue %s invalide pour le code pays %s" % (tags['addr:postcode'], self.Country)}))
        return err

    def way(self, data, tags, nds):
        return self.node(data, tags)

    def relation(self, data, tags, members):
        return self.node(data, tags)


###########################################################################
from plugins.Plugin import TestPluginCommon

class Test(TestPluginCommon):
    def test_FR(self):
        a = TagFix_Postcode(None)
        class _config:
            options = {"country": "FR"}
        class father:
            config = _config()
        a.father = father()
        a.init(None)
        print(a.node(None, {"addr:postcode":"la bas"}))
        self.check_err(a.node(None, {"addr:postcode":"la bas"}))
        assert not a.node(None, {"addr:postcode":"75000"})
        assert not a.node(None, {"postal_code":"75000"})
        assert a.node(None, {"addr:postcode":"75 000"})

    def test_no_country(self):
        a = TagFix_Postcode(None)
        class _config:
            options = {}
        class father:
            config = _config()
        a.father = father()
        a.init(None)
        assert not a.node(None, {"addr:postcode":"la bas"})
        assert not a.node(None, {"addr:postcode":"75000"})
        assert not a.node(None, {"postal_code":"75000"})

    def test_NL(self):
        a = TagFix_Postcode(None)
        class _config:
            options = {"country": "NL"}
        class father:
            config = _config()
        a.father = father()
        a.init(None)
        self.check_err(a.node(None, {"addr:postcode":"la bas"}))
        assert not a.node(None, {"addr:postcode":"1234 AB"})
        assert not a.node(None, {"addr:postcode":"1234AB"})
        assert a.node(None, {"addr:postcode":"12 34AB"})
        assert a.node(None, {"addr:postcode":"12241AB"})
        assert a.node(None, {"addr:postcode":"1224"})
        assert not a.node(None, {"postal_code":"1224"})

    def test_MD(self):
        a = TagFix_Postcode(None)
        class _config:
            options = {"country": "MD"}
        class father:
            config = _config()
        a.father = father()
        a.init(None)
        assert not a.node(None, {"addr:postcode":"3100"})
        assert not a.node(None, {"addr:postcode":"MD3100"})
        assert a.node(None, {"addr:postcode":"0"})
        assert a.node(None, {"addr:postcode":"12-190"})
        assert a.node(None, {"addr:postcode":"1211901"})

    def test_BI(self):
        a = TagFix_Postcode(None)
        class _config:
            options = {"country": "BI"}
        class father:
            config = _config()
        a.father = father()
        a.init(None)
        assert not a.node(None, {"addr:postcode":"3100"})
        assert not a.node(None, {"addr:postcode":"MD3100"})
