#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Black Myst <black.myst@free.fr> 2011                       ##
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

import hashlib

class Plugin(object):

    def __init__(self, father):
        self.father = father

    def init(self, logger):
        """
        Called before starting analyse.
        @param logger:
        """
        self.errors = {}
        pass

    def availableMethodes(self):
        """
        Get a list of overridden methods.
        This is usefull to optimize call from analyser_sax.
        """
        capabilities = []
        currentClass = self.__class__
        if currentClass.node!=Plugin.node: capabilities.append("node")
        if currentClass.way!=Plugin.way: capabilities.append("way")
        if currentClass.relation!=Plugin.relation: capabilities.append("relation")
        return capabilities

    def node(self, node, tags):
        """
        Called each time a node is found on data source.

        @param node: dict with details.
            example: node[u"id"], node[u"lat"], node[u"lon"], node[u"version"]
        @param tags: dict with all tags and values.
        @return: error list.
        """
        pass

    def way(self, way, tags, nodes):
        """
        Called each time a way is found on data source.

        @param way: dict with details.
            example: node[u"id"], node[u"lat"], node[u"lon"], node[u"version"]
        @param tags: dict with all tags and values.
        @param nodes: list of all nodes id.
        @return: error list.
        """
        pass

    def relation(self, relation, tags, members):
        """
        Called each time a relation is found on data source.

        @param relation: dict with details.
            example: node[u"id"], node[u"lat"], node[u"lon"], node[u"version"]
        @param tags: dict with all tags and values.
        @param members:  list of all relation members.
        @return: error list.
        """
        pass

    def end(self, logger):
        """
        Called after starting analyse.
        @param logger:
        """
        pass

    def ToolsStripAccents(self, mot):
        mot = mot.replace(u"à", u"a").replace(u"â", u"a")
        mot = mot.replace(u"é", u"e").replace(u"è", u"e").replace(u"ë", u"e").replace(u"ê", u"e")
        mot = mot.replace(u"î", u"i").replace(u"ï", u"i")
        mot = mot.replace(u"ô", u"o").replace(u"ö", u"o")
        mot = mot.replace(u"û", u"u").replace(u"ü", u"u")
        mot = mot.replace(u"ÿ", u"y")
        mot = mot.replace(u"ç", u"c")
        mot = mot.replace(U"À", U"A").replace(u"Â", u"A")
        mot = mot.replace(U"É", U"E").replace(U"È", U"E").replace(U"Ë", U"E").replace(U"Ê", U"E")
        mot = mot.replace(U"Î", U"I").replace(U"Ï", U"I")
        mot = mot.replace(U"Ô", U"O").replace(U"Ö", U"O")
        mot = mot.replace(U"Û", U"U").replace(U"Ü", U"U")
        mot = mot.replace(U"Ÿ", U"Y")
        mot = mot.replace(U"Ç", U"C")
        mot = mot.replace(U"œ", U"oe")
        mot = mot.replace(U"æ", U"ae")
        mot = mot.replace(U"Œ", U"OE")
        mot = mot.replace(U"Æ", U"AE")
        return mot

    def ToolsStripDouble(self, mot):
        mot = mot.replace(u"cc", u"c")
        mot = mot.replace(u"dd", u"d")
        mot = mot.replace(u"ee", u"e")
        mot = mot.replace(u"ff", u"f")
        mot = mot.replace(u"ll", u"l")
        mot = mot.replace(u"mm", u"m")
        mot = mot.replace(u"nn", u"n")
        mot = mot.replace(u"pp", u"p")
        mot = mot.replace(u"rr", u"r")
        mot = mot.replace(u"ss", u"s")
        mot = mot.replace(u"tt", u"t")
        return mot

    def stablehash(self, s):
        """
        Compute a stable positive integer hash on 32bits
        @param s: a string
        """
        return int(abs(int(hashlib.md5(s).hexdigest(), 16)) % 2147483647)


###########################################################################
import unittest

class TestPluginCommon(unittest.TestCase):
    def setUp(self):
        import analysers.Analyser


    # Check errors generation, and unicode encoding
    def check_err(self, errors, log=""):
        assert errors, log
        for error in errors:
            assert isinstance(error[0], int), error[0]
            assert isinstance(error[1], int), error[1]
            assert isinstance(error[2], dict), error[2]
            self.check_dict(error[2], log)

    def check_dict(self, d, log):
        for (k,v) in d.items():
            self.check_str(k, log)
            if isinstance(v, basestring):
                self.check_str(v, log)
            elif isinstance(v, dict):
                self.check_dict(v, log)
            else:
                self.check_array(v, log)

    def check_array(self, a, log):
        for v in a:
            if isinstance(v, basestring):
                self.check_str(v, log)
            elif isinstance(v, dict):
                self.check_dict(v, log)
            else:
                self.check_array(v, log)

    def check_str(self, s, log):
        if isinstance(s, str):
            try:
                s.decode('ascii')
            except:
                print log
                print s
                raise
