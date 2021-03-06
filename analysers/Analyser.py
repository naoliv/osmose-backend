#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Frederic Rodrigo 2011                                      ##
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

import __builtin__
import re, hashlib
from modules import OsmoseErrorFile
from modules import OsmoseTranslation

if not hasattr(__builtin__, "T_"):
    translate = OsmoseTranslation.OsmoseTranslation()
    __builtin__.T_ = translate.translate

class Analyser(object):

    def __init__(self, config, logger = None):
        self.config = config
        self.logger = logger
        if not hasattr(__builtin__, "T_"):
            self.translate = OsmoseTranslation.OsmoseTranslation()
            __builtin__.T_ = self.translate.translate

    def __enter__(self):
        self.open_error_file()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_error_file()
        pass

    def open_error_file(self):
        self.error_file = OsmoseErrorFile.ErrorFile(self.config)
        self.error_file.begin()

    def close_error_file(self):
        self.error_file.end()

    re_points = re.compile("[\(,][^\(,\)]*[\),]")

    def get_points(self, text):
        if not text:
            return []
        pts = []
        for r in self.re_points.findall(text):
            lon, lat = r[1:-1].split(" ")
            pts.append({"lat":lat, "lon":lon})
        return pts

    def analyser(self):
        pass

    def analyser_change(self):
        self.analyser()

    def stablehash(self, s):
        """
        Compute a stable positive integer hash on 32bits
        @param s: a string
        """
        return int(abs(int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)) % 2147483647)

###########################################################################
import unittest

class TestAnalyser(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        import __builtin__
        import sys
        sys.path.append(".")
        import modules.OsmoseLog
        if not hasattr(cls, "logger"):
            cls.logger = modules.OsmoseLog.logger(sys.stdout, True)

    @classmethod
    def teardown_class(cls):
        pass

    @staticmethod
    def init_config(osm_file=None, dst=None, analyser_options=None):
        import osmose_run
        import osmose_config
        conf = osmose_config.template_config("test", analyser_options=analyser_options)
        conf.db_base = "osmose_test"
        conf.db_schema = conf.country
        conf.download["osmosis"] = "test"
        conf.download["dst"] = osm_file
        conf.init()

        analyser_conf = osmose_run.analyser_config()
        analyser_conf.db_string = conf.db_string
        analyser_conf.db_user = conf.db_user
        analyser_conf.db_schema = conf.db_schema
        analyser_conf.polygon_id = None
        analyser_conf.options = conf.analyser_options
        analyser_conf.dst = dst

        return (conf, analyser_conf)

    @staticmethod
    def normalise_dict(d):
        """
        Recursively convert dict-like object (eg OrderedDict) into plain dict.
        Sorts list values.
        """
        out = {}
        for k, v in dict(d).iteritems():
            if hasattr(v, 'iteritems'):
                out[k] = TestAnalyser.normalise_dict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in sorted(v):
                    if hasattr(item, 'iteritems'):
                        out[k].append(TestAnalyser.normalise_dict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out

    @staticmethod
    def compare_list(a, b, ctx=u""):
        for k in xrange(min(len(a), len(b))):
            if a[k] != b[k]:
                if hasattr(a[k], 'iteritems') and hasattr(b[k], 'iteritems'):
                    return TestAnalyser.compare_dict(a[k], b[k], ctx + "." + unicode(k))
                elif isinstance(a[k], list) and isinstance(b[k], list):
                    return TestAnalyser.compare_list(a[k], b[k], ctx + "." + unicode(k))
                else:
                    return "key '%s' is different: '%s' != '%s' [%s]" % (k, a[k], b[k], ctx)
        if len(a) != len(b):
            return "length are different: %d != %d [%s]" % (len(a), len(b), ctx)
        return ""


    @staticmethod
    def compare_dict(a, b, ctx=u""):
        for k in a.iterkeys():
            if k not in b:
                return "key '%s' is missing from b [%s]" % (k, ctx)

        for k in b.iterkeys():
            if k not in a:
                return "key '%s' is missing from a [%s]" % (k, ctx)
            if a[k] != b[k]:
                if hasattr(a[k], 'iteritems') and hasattr(b[k], 'iteritems'):
                    return TestAnalyser.compare_dict(a[k], b[k], ctx + "." + unicode(k))
                elif isinstance(a[k], list) and isinstance(b[k], list):
                    return TestAnalyser.compare_list(a[k], b[k], ctx + "." + unicode(k))
                else:
                    return "key '%s' is different: '%s' != '%s' [%s]" % (k, a[k], b[k], ctx)

        return ""

    @staticmethod
    def remove_non_checked_entries(a):
        a["analysers"]["@timestamp"] = "xxx"
        a["analysers"]["analyser"]["@timestamp"] = "xxx"

        # remove translations other than fr/en
        if isinstance(a["analysers"]["analyser"]["class"], list):
            for c in a["analysers"]["analyser"]["class"]:
                if isinstance(c["classtext"], list):
                    for t in xrange(len(c["classtext"])-1, -1, -1):
                        if c["classtext"][t]["@lang"] not in ("en"):
                            del c["classtext"][t]
        else:
            c = a["analysers"]["analyser"]["class"]
            if isinstance(c["classtext"], list):
                for t in xrange(len(c["classtext"])-1, -1, -1):
                    if c["classtext"][t]["@lang"] not in ("en"):
                        del c["classtext"][t]

    def compare_results(self, orig_xml=None):
        if orig_xml is None:
            raise  # TODO

        import xmltodict

        a = xmltodict.parse(open(orig_xml))
        b = xmltodict.parse(open(self.xml_res_file))
        a = TestAnalyser.normalise_dict(a)
        b = TestAnalyser.normalise_dict(b)

        TestAnalyser.remove_non_checked_entries(a)
        TestAnalyser.remove_non_checked_entries(b)

        if a != b:
            print TestAnalyser.compare_dict(a, b)
            self.assertEquals(a, b, "results differ")


    def load_errors(self):
        import xml.etree.ElementTree as ET
        tree = ET.parse(self.xml_res_file)
        return tree.getroot()

    def check_err(self, cl=None, lat=None, lon=None, elems=None):
        for e in self.root_err.find("analyser").findall('error'):
            if cl is not None and e.attrib["class"] != cl:
               continue
            if lat is not None and e.find("location").attrib["lat"] != lat:
               continue
            if lon is not None and e.find("location").attrib["lon"] != lon:
               continue
            if elems is not None:
               xml_elems = []
               for t in ("node", "way", "relation"):
                   for err_elem in e.findall(t):
                       xml_elems.append((t, err_elem.attrib["id"]))
               if set(elems) != set(xml_elems):
                   continue
            return True

        assert False, "Error not found"

    def check_num_err(self, num=None, min=None):
        xml_num = len(self.root_err.find("analyser").findall('error'))
        if num is not None:
            self.assertEquals(xml_num, num, "Found %d errors instead of %d" % (xml_num, num))
        if min is not None:
            self.assertGreaterEqual(xml_num, min, "Found %d errors instead of > %d" % (xml_num, min))


###########################################################################

class Test(unittest.TestCase):
    def test_stablehash(self):
        a = Analyser(None)
        h1 = a.stablehash( "toto")
        h2 = a.stablehash(u"toto")
        h3 = a.stablehash(u"é")
        self.assertEquals(h1, h2)
        self.assertNotEquals(h1, h3)

    def test_compare_dict(self):
        a = TestAnalyser
        self.assertEquals(a.compare_dict({1:1, 2:2}, {1:1, 2:2}), u"")
        self.assertEquals(a.compare_dict({1:1, 2:2}, {2:2, 1:1}), u"")
        self.assertEquals(a.compare_dict({1:1, 2:2}, {1:0, 2:2}), u"key '1' is different: '1' != '0' []")
        self.assertEquals(a.compare_dict({1:1, 2:2}, {1:1, 3:3}), u"key '2' is missing from b []")
        self.assertEquals(a.compare_dict({1:1,    }, {1:1, 2:2}), u"key '2' is missing from a []")
        self.assertEquals(a.compare_dict({1:1, 2:2}, {1:1,    }), u"key '2' is missing from b []")

        self.assertEquals(a.compare_dict({1:[3,4], 2:2}, {1:[3,4], 2:2}), u"")
        self.assertEquals(a.compare_dict({1:[3,4], 2:2}, {1:[3,5], 2:2}), u"key '1' is different: '4' != '5' [.1]")
        self.assertEquals(a.compare_dict({1:[3  ], 2:2}, {1:[3,4], 2:2}), u"length are different: 1 != 2 [.1]")
        self.assertEquals(a.compare_dict({1:[3,4], 2:2}, {1:[3  ], 2:2}), u"length are different: 2 != 1 [.1]")

        self.assertEquals(a.compare_dict({1:{3:4}, 2:2}, {1:{3:4}, 2:2}), u"")
        self.assertEquals(a.compare_dict({1:{3:4}, 2:2}, {1:{3:5}, 2:2}), u"key '3' is different: '4' != '5' [.1]")
        self.assertEquals(a.compare_dict({1:{3:4}, 2:2}, {1:{4:5}, 2:2}), u"key '3' is missing from b [.1]")
        self.assertEquals(a.compare_dict({1:{   }, 2:2}, {1:{3:4}, 2:2}), u"key '3' is missing from a [.1]")
        self.assertEquals(a.compare_dict({1:{3:4}, 2:2}, {1:{   }, 2:2}), u"key '3' is missing from b [.1]")
