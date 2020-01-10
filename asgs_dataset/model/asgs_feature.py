from datetime import datetime
from functools import lru_cache, partial
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import rdflib
from flask import Response, render_template, redirect, url_for
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, XSD, OWL, Literal, BNode
from rdflib.namespace import DCTERMS

import asgs_dataset._config as conf
from lxml import etree
import os

from asgs_dataset.helpers import wfs_extract_features_as_geojson, \
    gml_extract_geom_to_geojson, gml_extract_geom_to_geosparql, RDF_a, \
    GEO, ASGS, GEO_Feature, GEO_hasGeometry, \
    wfs_extract_features_with_rdf_converter, calculate_bbox, GEOX, \
    gml_extract_shapearea_to_geox_area, DATA, CRS_EPSG, LOCI, ASGS_CAT, \
    ASGS_ID, GEO_within, GEO_contains
from asgs_dataset.model import ASGSModel, NotFoundError

MESHBLOCK_COUNT = 358009
SA1_COUNT = 57490
SA2_COUNT = 2292
SA3_COUNT = 340
SA4_COUNT = 89

INVERSE_TOKEN = object()

RDF_INCLUDE_UNKNOWN_PREDICATES = False

# WHY ARE THEY ALL WFS?!
xml_ns = {
    "MB": "WFS",
    "SA1": "WFS",
    "SA2": "WFS",
    "SA3": "WFS",
    "SA4": "WFS",
    "STATE": "WFS",
    "AUS": "WFS"
}

geometry_service_routes = {
    "MB": "asgs16_mb/",
    "SA1": "asgs16_sa1/",
    "SA2": "asgs16_sa2/",
    "SA3": "asgs16_sa3/",
    "SA4": "asgs16_sa4/",
    "STATE": "asgs16_ste/",
    "AUS": "asgs16_aus/"
}
feature_identification_types = {
    "MB": ASGS_ID.term("mbCode2016"),
    "SA1": ASGS_ID.term("sa1Maincode2016"),
    "SA2": ASGS_ID.term("sa2Maincode2016"),
    "SA3": ASGS_ID.term("sa3Code2016"),
    "SA4": ASGS_ID.term("sa4Code2016"),
    "STATE": ASGS_ID.term("stateCode2016"),
    "AUS": ASGS_ID.term("ausCode2016")
}


asgs_tag_map = {
    "{WFS}OBJECTID": "object_id",
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
    "{WFS}Shape_Length": 'shape_length',
    "{WFS}Shape_Area": 'shape_area',
    "{WFS}Shape": 'shape',
}

mb_tag_map = {
    "{WFS}MB_CODE_2016": 'code',
    "{WFS}MB_CATEGORY_CODE_2016": "category",
    "{WFS}MB_CATEGORY_NAME_2016": "category_name",
    "{WFS}SA1_MAINCODE_2016": "sa1",
    "{WFS}STATE_CODE_2016": "state",
    "{WFS}DZN_CODE_2016": "dzn",
    "{WFS}SSC_CODE_2016": "ssc",
    "{WFS}NRMR_CODE_2016": "nrmr",
    "{WFS}ADD_CODE_2016": "add"
}
mb_predicate_map_asgs = {
    'code': [ASGS.mbCode2016],
    'category_name': [ASGS.category],
    'sa1': INVERSE_TOKEN,
    'state': INVERSE_TOKEN,
    'dzn': INVERSE_TOKEN,
    'ssc': INVERSE_TOKEN,
    'nrmr': INVERSE_TOKEN,
}
mb_predicate_map_loci = {
    'code': [DCTERMS.identifier],
    'category': [DCTERMS.type],
    'sa1': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
    'dzn': [GEO_within, INVERSE_TOKEN],
    'ssc': [GEO_within, INVERSE_TOKEN],
    'nrmr': [GEO_within, INVERSE_TOKEN],
}

sa1_tag_map = {
    "{WFS}SA1_MAINCODE_2016": 'code',
    "{WFS}SA2_MAINCODE_2016": "sa2",
    "{WFS}STATE_CODE_2016": "state",
    "{WFS}SA1_7DIGITCODE_2016": "seven_code",
}
sa1_predicate_map_asgs = {
    'code': [ASGS.sa1Maincode2016, ASGS.statisticalArea1Sa111DigitCode],
    'sa2': INVERSE_TOKEN,
    'state': INVERSE_TOKEN,
}
sa1_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.statisticalArea1Sa111DigitCode],
    'sa2': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
}

sa2_tag_map = {
    "{WFS}SA2_MAINCODE_2016": 'code',
    "{WFS}SA2_NAME_2016": 'name',
    "{WFS}SA3_CODE_2016": "sa3",
    "{WFS}STATE_CODE_2016": "state",
}
sa2_predicate_map_asgs = {
    'code': [ASGS.sa2Maincode2016, ASGS.statisticalArea2Sa29DigitCode],
    'name': [ASGS.sa2Name2016],
    'sa3': INVERSE_TOKEN,
    'state': INVERSE_TOKEN,
}
sa2_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.statisticalArea2Sa29DigitCode],
    'name': [ASGS.sa2Name2016],
    'sa3': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
}


sa3_tag_map = {
    "{WFS}SA3_CODE_2016": 'code',
    "{WFS}SA3_NAME_2016": 'name',
    "{WFS}SA4_CODE_2016": "sa4",
    "{WFS}STATE_CODE_2016": "state",
}
sa3_predicate_map_asgs = {
    'code': [ASGS.sa3Code2016, ASGS.statisticalArea3Sa35DigitCode],
    'name': [ASGS.sa3Name2016],
    'sa4': INVERSE_TOKEN,
    'state': INVERSE_TOKEN,
}
sa3_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.statisticalArea3Sa35DigitCode],
    'name': [ASGS.sa3Name2016],
    'sa4': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
}

sa4_tag_map = {
    "{WFS}SA4_CODE_2016": 'code',
    "{WFS}SA4_NAME_2016": 'name',
    "{WFS}GCCSA_CODE_2016": "gccsa",
    "{WFS}STATE_CODE_2016": "state",
}
sa4_predicate_map_asgs = {
    'code': [ASGS.sa4Code2016, ASGS.statisticalArea4Sa43DigitCode],
    'name': [ASGS.sa4Name2016],
    'state': INVERSE_TOKEN,
    'gccsa': INVERSE_TOKEN,
}
sa4_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.statisticalArea4Sa43DigitCode],
    'name': [ASGS.sa4Name2016],
    'state': [GEO_within, INVERSE_TOKEN],
    'gccsa': [GEO_within, INVERSE_TOKEN],
}


state_tag_map = {
    "{WFS}STATE_CODE_2016": 'code',
    "{WFS}STATE_NAME_2016": 'name',
    "{WFS}STATE_NAME_ABBREV_2016": 'name_abbrev'
}
state_predicate_map = {
    'code': [ASGS.stateCode2016, ASGS.stateOrTerritory1DigitCode],
    'name': [ASGS.stateName2016],
    'name_abbrev': [ASGS.label]
}


def asgs_features_geojson_converter(asgs_type, wfs_features):
    if len(wfs_features) < 1:
        return None
    to_converter = {
        'shape': gml_extract_geom_to_geojson,
    }
    to_float = ('shape_length', 'shape_area', 'albers_area')
    to_int = ('object_id', 'category', 'state')
    to_datetime = tuple()
    is_geom = ('shape',)
    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    tag_map = asgs_tag_map
    ignore_geom = False
    if asgs_type == "MB":
        tag_map = {**tag_map, **mb_tag_map}
    elif asgs_type == "SA1":
        tag_map = {**tag_map, **sa1_tag_map}
    elif asgs_type == "SA2":
        tag_map = {**tag_map, **sa2_tag_map}
    elif asgs_type == "SA3":
        tag_map = {**tag_map, **sa3_tag_map}
    elif asgs_type == "SA4":
        tag_map = {**tag_map, **sa4_tag_map}
    elif asgs_type == "STATE":
        tag_map = {**tag_map, **state_tag_map}
        ignore_geom = True
    elif asgs_type == "AUS":
        ignore_geom = True

    for object_id, feat_elem in features_source:  # type: int, etree._Element
        gj_dict = {"type": "Feature", "id": object_id, "geometry": {},
                   "properties": {}}
        for r in feat_elem.iterchildren():  # type: etree._Element
            try:
                var = tag_map[r.tag]
            except KeyError:
                continue
            if var in is_geom and ignore_geom:
                continue
            try:
                conv_func = to_converter[var]
                val = conv_func(r)
            except KeyError:
                val = r.text
            if var in to_datetime:
                if val.endswith('Z'):
                    val = val[:-1]
                try:
                    val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    val = "Invalid time format"
            elif var in to_float:
                val = float(val)
            elif var in to_int:
                val = int(val)
            if var in is_geom:
                gj_dict['geometry'] = val
            else:
                gj_dict['properties'][var] = val
        features_list.append(gj_dict)
    return features_list


def asgs_features_geosparql_converter(asgs_type, canonical_uri, wfs_features):
    if len(wfs_features) < 1:
        return None
    to_converter = {
        'shape': gml_extract_geom_to_geosparql,
        'shape_area': partial(gml_extract_shapearea_to_geox_area, crs=CRS_EPSG["3857"]), #cartesian area from asgs using "pseudo-mercator" projection
        'albers_area': partial(gml_extract_shapearea_to_geox_area, extra_transform=lambda x: (set(), float(x)*1000000), crs=CRS_EPSG["3577"]) #cartesian GDA-94 CRS using "Albers_Conic_Equal_Area" projection
    }
    to_float = ('shape_length',)
    to_int = ('object_id', 'category', 'state')
    is_geom = ('shape',)
    predicate_map = {
        'shape_area': [GEOX.hasAreaM2],
        'albers_area': [GEOX.hasAreaM2],
    }
    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    tag_map = asgs_tag_map
    ignore_geom = False
    if asgs_type == "MB":
        tag_map = {**tag_map, **mb_tag_map}
        predicate_map = {**predicate_map, **mb_predicate_map_asgs}
    elif asgs_type == "SA1":
        tag_map = {**tag_map, **sa1_tag_map}
        predicate_map = {**predicate_map, **sa1_predicate_map_asgs}
    elif asgs_type == "SA2":
        tag_map = {**tag_map, **sa2_tag_map}
        predicate_map = {**predicate_map, **sa2_predicate_map_asgs}
    elif asgs_type == "SA3":
        tag_map = {**tag_map, **sa3_tag_map}
        predicate_map = {**predicate_map, **sa3_predicate_map_asgs}
    elif asgs_type == "SA4":
        tag_map = {**tag_map, **sa4_tag_map}
        predicate_map = {**predicate_map, **sa4_predicate_map_asgs}
    elif asgs_type == "STATE":
        tag_map = {**tag_map, **state_tag_map}
        predicate_map = {**predicate_map, **state_predicate_map}
        ignore_geom = True
    elif asgs_type == "AUS":
        ignore_geom = True

    triples = set()
    feature_nodes = []
    for object_id, feat_elem in features_source:  # type: int, etree._Element
        feature_uri = rdflib.URIRef(canonical_uri)
        triples.add((feature_uri, RDF_a, GEO_Feature))
        for c in feat_elem.iterchildren():  # type: etree._Element
            try:
                var = tag_map[c.tag]
            except KeyError:
                continue
            if var in is_geom and ignore_geom:
                continue
            try:
                conv_func = to_converter[var]
                _triples, val = conv_func(c)
                for (s, p, o) in iter(_triples):
                    triples.add((s, p, o))
            except KeyError:
                val = c.text
            if var in to_float:
                val = Literal(float(val))
            elif var in to_int:
                try:
                    val = int(val)
                except ValueError:
                    val = str(val)
                val = Literal(val)
            else:
                if not isinstance(val, (URIRef, Literal, BNode)):
                    val = Literal(str(val))
            if var in is_geom:
                triples.add((feature_uri, GEO_hasGeometry, val))
            elif var in predicate_map.keys():
                predicate = predicate_map[var]
                if predicate == INVERSE_TOKEN:
                    continue
                if not isinstance(predicate, list):
                    predicate = [predicate]
                for p in predicate:
                    if p == INVERSE_TOKEN:
                        continue
                    triples.add((feature_uri, p, val))
            else:
                if RDF_INCLUDE_UNKNOWN_PREDICATES:
                    dummy_prop = URIRef("{}/{}".format("WFS", var))
                    triples.add((feature_uri, dummy_prop, val))
        features_list.append(feature_uri)
    return triples, feature_nodes


def asgs_features_loci_converter(asgs_type, canonical_uri, wfs_features):
    if len(wfs_features) < 1:
        return None
    lazy_id = str(canonical_uri).split('/')[-1]
    no_triples = set()
    to_converter = {
        'shape': lambda x: (no_triples, URIRef("".join([conf.GEOMETRY_SERVICE_URI, geometry_service_routes[asgs_type], lazy_id]))),
        'shape_area': partial(gml_extract_shapearea_to_geox_area, crs=CRS_EPSG["3857"]),  # cartesian area from asgs using "pseudo-mercator" projection
        'albers_area': partial(gml_extract_shapearea_to_geox_area, extra_transform=lambda x: (set(), float(x)*1000000.0), crs=CRS_EPSG["3577"]),  #c artesian GDA-94 CRS using "Albers_Conic_Equal_Area" projection
        'sa1': lambda x: (no_triples, URIRef(conf.URI_SA1_INSTANCE_BASE + x.text)),
        'sa2': lambda x: (no_triples, URIRef(conf.URI_SA2_INSTANCE_BASE + x.text)),
        'sa3': lambda x: (no_triples, URIRef(conf.URI_SA3_INSTANCE_BASE + x.text)),
        'sa4': lambda x: (no_triples, URIRef(conf.URI_SA4_INSTANCE_BASE + x.text)),
        'dzn': lambda x: (no_triples, URIRef(conf.URI_DZN_INSTANCE_BASE + x.text)),
        'ssc': lambda x: (no_triples, URIRef(conf.URI_SSC_INSTANCE_BASE + x.text)),
        'nrmr': lambda x: (no_triples, URIRef(conf.URI_NRMR_INSTANCE_BASE + x.text)),
        'state': lambda x: (no_triples, URIRef(conf.URI_STATE_INSTANCE_BASE + x.text)),
        'code': lambda x: (no_triples, Literal(x.text, datatype=feature_identification_types[asgs_type])),
        'category': lambda x: (no_triples, ASGS_CAT.term(x.text))
    }
    to_float = ('shape_length',)
    to_int = ('object_id',)
    is_geom = ('shape',)
    predicate_map = {
        'shape_area': [GEOX.hasAreaM2],
        'albers_area': [GEOX.hasAreaM2],
    }
    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    tag_map = asgs_tag_map
    if asgs_type == "MB":
        tag_map = {**tag_map, **mb_tag_map}
        predicate_map = {**predicate_map, **mb_predicate_map_loci}
    elif asgs_type == "SA1":
        tag_map = {**tag_map, **sa1_tag_map}
        predicate_map = {**predicate_map, **sa1_predicate_map_loci}
    elif asgs_type == "SA2":
        tag_map = {**tag_map, **sa2_tag_map}
        predicate_map = {**predicate_map, **sa2_predicate_map_loci}
    elif asgs_type == "SA3":
        tag_map = {**tag_map, **sa3_tag_map}
        predicate_map = {**predicate_map, **sa3_predicate_map_loci}
    elif asgs_type == "SA4":
        tag_map = {**tag_map, **sa4_tag_map}
        predicate_map = {**predicate_map, **sa4_predicate_map_loci}
    elif asgs_type == "STATE":
        tag_map = {**tag_map, **state_tag_map}
        predicate_map = {**predicate_map, **state_predicate_map}
    elif asgs_type == "AUS":
        pass

    triples = set()
    feature_nodes = []
    for object_id, feat_elem in features_source:  # type: int, etree._Element
        feature_uri = rdflib.URIRef(canonical_uri)
        triples.add((feature_uri, RDF_a, GEO_Feature))
        triples.add((feature_uri, RDF_a, ASGS.Feature))
        for c in feat_elem.iterchildren():  # type: etree._Element
            try:
                var = tag_map[c.tag]
            except KeyError:
                continue
            try:
                conv_func = to_converter[var]
                try:
                    _triples, val = conv_func(c)
                except Exception as e:
                    print(e)
                    raise
                for (s, p, o) in iter(_triples):
                    triples.add((s, p, o))
            except KeyError:
                val = c.text
            if var in to_float:
                val = Literal(float(val))
            elif var in to_int:
                try:
                    val = int(val)
                except ValueError:
                    val = str(val)
                val = Literal(val)
            else:
                if not isinstance(val, (URIRef, Literal, BNode)):
                    val = Literal(str(val))
            if var in is_geom:
                triples.add((feature_uri, GEO_hasGeometry, val))
            elif var in predicate_map.keys():
                predicate = predicate_map[var]
                if predicate == INVERSE_TOKEN:
                    continue
                if not isinstance(predicate, list):
                    predicate = [predicate]
                for p in predicate:
                    if p == INVERSE_TOKEN:
                        continue
                    triples.add((feature_uri, p, val))
            else:
                pass  # do nothing with predicates we don't know
        features_list.append(feature_uri)
    return triples, feature_nodes

def extract_asgs_features_as_geojson(asgs_type, tree):
    geojson_features = wfs_extract_features_as_geojson(
        tree, 'WFS', asgs_type,
        partial(asgs_features_geojson_converter, asgs_type))
    return geojson_features


def extract_asgs_features_as_rdf(asgs_type, canonical_uri, tree, ont_conv, g):
    triples, features = wfs_extract_features_with_rdf_converter(
        tree, 'WFS', asgs_type,
        partial(ont_conv, asgs_type, canonical_uri))
    for (s, p, o) in iter(triples):
        g.add((s, p, o))
    return g

@lru_cache(maxsize=128)
def retrieve_asgs_feature(asgs_type, identifier, local=True):
    if identifier.startswith("http:") or identifier.startswith("https:"):
        identifier = identifier.split('/')[-1]

    tree = None
    if asgs_type == "STATE" or asgs_type == "AUS":
        parser = etree.XMLParser(recover=True, huge_tree=True)
    else:
        parser = etree.XMLParser(recover=True)
    if local:  # a stub to use a local file for testing
        xml_file = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
            'test',
            asgs_type + '_' + identifier + '.xml')
        try:
            tree = etree.parse(xml_file, parser=parser)
        except (FileNotFoundError, OSError):
            tree = None
        except Exception as e:
            print(e)
            raise
    if tree is None:
        wfs_uri = ASGSFeature.construct_wfs_query_for_feature_type(
            asgs_type, identifier)
        try:
            r = Request(wfs_uri, method='GET')
            with urlopen(r) as resp:
                if not (200 <= resp.status <= 299):
                    if resp.status == 404:
                        raise NotFoundError()
                    raise RuntimeError(
                        "Cannot get feature index from WFS backend.")
                try:
                    tree = etree.parse(resp, parser=parser)
                except Exception:
                    raise RuntimeError("Cannot decode XML from WFS endpoint")
        except HTTPError as he:
            if he.code == 404:
                raise NotFoundError()
            raise
        except Exception as e:
            print(e)
            raise
    return tree


class ASGSFeature(ASGSModel):

    @classmethod
    def make_instance_label(cls, instance_uri, instance_id):
        asgs_type = cls.determine_asgs_type(instance_uri)
        if asgs_type == "MB":
            return "Meshblock #{}".format(instance_id)
        elif asgs_type == "SA1":
            return "SA1 Feature #{}".format(instance_id)
        elif asgs_type == "SA2":
            return "SA2 Feature #{}".format(instance_id)
        elif asgs_type == "SA3":
            return "SA3 Feature #{}".format(instance_id)
        elif asgs_type == "SA4":
            return "SA4 Feature #{}".format(instance_id)
        elif asgs_type == "STATE":
            return "State - {}".format(instance_id)
        elif asgs_type == "AUS":
            return "Australia ({})".format(instance_id)
        return "ASGS Feature #{}".format(instance_id)

    @classmethod
    def get_index(cls, base_uri, page, per_page):
        per_page = max(int(per_page), 1)
        offset = (max(int(page), 1)-1)*per_page
        asgs_type = cls.determine_asgs_type(base_uri)
        return cls.get_feature_index(asgs_type, offset, per_page)

    @classmethod
    def make_canonical_uri(cls, instance_uri, instance_id):
        return instance_uri

    @classmethod
    def make_local_url(cls, instance_uri, instance_id):
        asgs_type = cls.determine_asgs_type(instance_uri)
        if asgs_type == "MB":
            return url_for("controller.redirect_meshblock", mb=instance_id)
        elif asgs_type == "SA1":
            return url_for("controller.redirect_sa1", sa1=instance_id)
        elif asgs_type == "SA2":
            return url_for("controller.redirect_sa2", sa2=instance_id)
        elif asgs_type == "SA3":
            return url_for("controller.redirect_sa3", sa3=instance_id)
        elif asgs_type == "SA4":
            return url_for("controller.redirect_sa4", sa4=instance_id)
        elif asgs_type == "STATE":
            return url_for("controller.redirect_state", state=instance_id)
        elif asgs_type == "AUS":
            return url_for("controller.redirect_aus", code=instance_id)
        return url_for("controller.object", uri=instance_uri)

    def __init__(self, uri):
        super(ASGSFeature, self).__init__()
        # split ID out of URI for all ASGS Features
        self.uri = uri
        self.id = uri.split('/')[-1]
        self._assign_asgs_type()
        feature_xml_tree = retrieve_asgs_feature(self.asgs_type, self.id)
        self.xml_tree = feature_xml_tree
        wfs_features = extract_asgs_features_as_geojson(
            self.asgs_type, feature_xml_tree)
        try:
            asgs_feature = wfs_features['features'][0]
        except (AttributeError, KeyError, TypeError) as e:
            raise NotFoundError()
        self.geometry = asgs_feature['geometry']
        self.properties = asgs_feature['properties']

    @classmethod
    def determine_asgs_type(cls, instance_uri):
        if '/meshblock/' in instance_uri:
            return 'MB'
        elif '/statisticalarealevel1/' in instance_uri:
            return 'SA1'
        elif '/statisticalarealevel2/' in instance_uri:
            return 'SA2'
        elif '/statisticalarealevel3/' in instance_uri:
            return 'SA3'
        elif '/statisticalarealevel4/' in instance_uri:
            return 'SA4'
        elif '/stateorterritory/' in instance_uri:
            return 'STATE'
        else:  # australia
            return 'AUS'

    def _assign_asgs_type(self):
        self.asgs_type = self.determine_asgs_type(self.uri)

    def as_geosparql(self, graph=None):
        if graph is None:
            graph = rdflib.Graph()
            graph.bind('asgs', ASGS)
            graph.bind('geo', GEO)
            graph.bind('geox', GEOX)
            graph.bind('data', DATA)
        return extract_asgs_features_as_rdf(
            self.asgs_type, self.uri, self.xml_tree,
            asgs_features_geosparql_converter, graph)

    def as_loci(self, graph=None):
        if graph is None:
            graph = rdflib.Graph()
            graph.bind('asgs', ASGS)
            graph.bind('geo', GEO)
            graph.bind('geox', GEOX)
            graph.bind('data', DATA)
            graph.bind('loci', LOCI)
            graph.bind('dcterms', DCTERMS)
            graph.bind('asgs-cat', ASGS_CAT)
            graph.bind('asgs-id', ASGS_ID)
        return extract_asgs_features_as_rdf(
            self.asgs_type, self.uri, self.xml_tree,
            asgs_features_loci_converter, graph)

    def get_bbox(self, pad=0):
        coords = self.geometry['coordinates']
        crs = self.geometry.get('crs', None)
        if crs:
            p = crs['properties']
            srs = p['name']
        else:
            srs = None
        json_bbox = calculate_bbox(coords, pad=pad, srs=srs)
        (n, s, e, w) = json_bbox
        return (w,s,e,n) # (minx, miny, maxx, maxy)

    def _get_instance_rdf(self, profile='loci'):
        deets = self.properties
        if profile in {'loci', 'asgs', 'geosparql'}:
            is_loci_profile = profile == "loci"
            if profile in {'asgs', 'geosparql'}:
                g = self.as_geosparql(g)
            elif is_loci_profile:
                g = self.as_loci()
            else:
                g = rdflib.Graph()
                g.bind('asgs', ASGS)
                g.bind('geo', GEO)
                g.bind('geox', GEOX)
                g.bind('data', DATA)
                g.bind('loci', LOCI)
                g.bind('asgs-cat', ASGS_CAT)
                g.bind('asgs-id', ASGS_ID)
            # ID & definition of the MB
            feat = URIRef(self.uri)

            if self.asgs_type == "MB":
                g.add((feat, RDF_a, ASGS.MeshBlock))
                sa1 = URIRef(conf.URI_SA1_INSTANCE_BASE + deets['sa1'])

                if 'dzn' in deets:
                    dzn_type = URIRef(conf.URI_DZN_CLASS)
                    dzn_code = Literal(str(deets['dzn']))
                    # TODO, give DZN's their own register
                    dzn = URIRef(conf.URI_DZN_INSTANCE_BASE+str(deets['dzn']))
                    g.add((dzn, RDF_a, dzn_type))
                    if is_loci_profile:
                        dzn_code._datatype = ASGS_ID.term('dznCode2016')
                        g.add((dzn, DCTERMS.identifier, dzn_code))
                        g.add((dzn, GEO_contains, feat))
                    else:
                        g.add((dzn, ASGS.dznCode2016, dzn_code))
                        g.add((dzn, ASGS.contains, feat))
                if 'ssc' in deets:
                    ss_type = URIRef(conf.URI_SSC_CLASS)
                    ss_code = Literal(str(deets['ssc']))
                    # TODO, give SSC's their own register
                    ss = URIRef(conf.URI_SSC_INSTANCE_BASE+str(deets['ssc']))
                    g.add((ss, RDF_a, ss_type))

                    if is_loci_profile:
                        ss_code._datatype = ASGS_ID.term('sscCode2016')
                        g.add((ss, DCTERMS.identifier, ss_code))
                        g.add((ss, GEO_contains, feat))
                    else:
                        g.add((ss, ASGS.sscCode2016, ss_code))
                        g.add((ss, ASGS.contains, feat))
                if 'nrmr' in deets:
                    nrmr_type = URIRef(conf.URI_NRMR_CLASS)
                    nrmr_code = Literal(str(deets['nrmr']))
                    # TODO, give NRMR's their own register
                    nrmr = URIRef(conf.URI_NRMR_INSTANCE_BASE+str(deets['nrmr']))
                    g.add((nrmr, RDF_a, nrmr_type))

                    if is_loci_profile:
                        g.add((nrmr, GEO_contains, feat))
                        nrmr_code._datatype = ASGS_ID.term('nrmrCode2016')
                        g.add((nrmr, DCTERMS.identifier, nrmr_code))
                    else:
                        g.add((nrmr, ASGS.contains, feat))
                        g.add((nrmr, ASGS.nrmrCode2016, nrmr_code))
                # register
                if is_loci_profile:
                    g.add((sa1, GEO_contains, feat))
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_MESHBLOCK_INSTANCE_BASE)))
                else:
                    g.add((sa1, ASGS.isStatisticalAreaLevel1Of, feat))
                    g.add((feat, URIRef('http://purl.org/linked-data/registry#register'), URIRef(conf.URI_MESHBLOCK_INSTANCE_BASE)))
            elif self.asgs_type == "SA1":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel1))
                sa2 = URIRef(conf.URI_SA2_INSTANCE_BASE + deets['sa2'])
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SA1_INSTANCE_BASE)))
                    g.add((sa2, GEO_contains, feat))
                else:
                    g.add((feat, URIRef('http://purl.org/linked-data/registry#register'), URIRef(conf.URI_SA1_INSTANCE_BASE)))
                    g.add((sa2, ASGS.isStatisticalAreaLevel2Of, feat))
            elif self.asgs_type == "SA2":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel2))
                sa3 = URIRef(conf.URI_SA3_INSTANCE_BASE + deets['sa3'])
                g.add((sa3, ASGS.isStatisticalAreaLevel3Of, feat))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SA2_INSTANCE_BASE)))
                    g.add((sa3, GEO_contains, feat))
                else:
                    g.add((feat, URIRef('http://purl.org/linked-data/registry#register'), URIRef(conf.URI_SA2_INSTANCE_BASE)))
                    g.add((sa3, ASGS.isStatisticalAreaLevel3Of, feat))
            elif self.asgs_type == "SA3":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel3))
                sa4 = URIRef(conf.URI_SA4_INSTANCE_BASE + deets['sa4'])
                g.add((sa4, ASGS.isStatisticalAreaLevel4Of, feat))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SA3_INSTANCE_BASE)))
                    g.add((sa4, GEO_contains, feat))
                else:
                    g.add((feat, URIRef('http://purl.org/linked-data/registry#register'), URIRef(conf.URI_SA3_INSTANCE_BASE)))
                    g.add((sa4, ASGS.isStatisticalAreaLevel4Of, feat))
            elif self.asgs_type == "SA4":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel4))
                if 'gccsa' in deets:
                    gccsa_type = URIRef(conf.URI_GCCSA_CLASS)
                    gccsa_code = Literal(str(deets['gccsa']))
                    #TODO, give GCCSA's their own register
                    gccsa = URIRef(conf.URI_GCCSA_INSTANCE_BASE+str(deets['gccsa']))
                    g.add((gccsa, RDF_a, gccsa_type))
                    g.add((gccsa, ASGS.greaterCapitalCityStatisticalAreasGccsa5CharacterAlphanumericCode, gccsa_code))
                    if is_loci_profile:
                        g.add((gccsa, GEO_contains, feat))
                        gccsa_code._datatype = ASGS_ID.term('gccsaCode2016')
                        g.add((gccsa, DCTERMS.identifier, gccsa_code))
                    else:
                        g.add((gccsa, ASGS.isGreaterCapitalCityStatisticalAreaOf, feat))
                        g.add((gccsa, ASGS.gccsaCode2016, gccsa_code))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SA4_INSTANCE_BASE)))
                else:
                    g.add((feat, URIRef('http://purl.org/linked-data/registry#register'), URIRef(conf.URI_SA4_INSTANCE_BASE)))
            elif self.asgs_type == "STATE":
                g.add((feat, RDF_a, ASGS.StateOrTerritory))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_STATE_INSTANCE_BASE)))
                else:
                    g.add((feat, URIRef('http://purl.org/linked-data/registry#register'), URIRef(conf.URI_STATE_INSTANCE_BASE)))
            else:
                g.add((feat, RDF_a, ASGS.Australia))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_AUS_INSTANCE_BASE)))
                else:
                    g.add((feat, URIRef('http://purl.org/linked-data/registry#register'), URIRef(conf.URI_AUS_INSTANCE_BASE)))
            if self.asgs_type != "AUS" and self.asgs_type != "STATE":
                if 'state' in deets:
                    state_uri = URIRef(conf.URI_STATE_INSTANCE_BASE + str(deets['state']))
                    if is_loci_profile:
                        g.add((state_uri, GEO_contains, feat))
                    else:
                        g.add((state_uri, ASGS.isStateOrTerritoryOf, feat))

        # TODO: add in these other views
        # elif profile == 'schemaorg':
        # elif profile == 'wfs':
            return g
        else:
            return NotImplementedError(
                "RDF Export for profile \"{}\" is not implemented.".
                format(profile))

    @staticmethod
    def total_meshblocks():
        return MESHBLOCK_COUNT

    @staticmethod
    def total_sa1s():
        return SA1_COUNT

    @staticmethod
    def total_sa2s():
        return SA2_COUNT

    @staticmethod
    def total_sa3s():
        return SA3_COUNT

    @staticmethod
    def total_sa4s():
        return SA4_COUNT

    @staticmethod
    def total_states():
        return 9

    @classmethod
    def get_feature_index(cls, asgs_type, startindex, count):
        url = cls.construct_wfs_query_for_index(asgs_type, startindex, count)
        req = Request(url, method='GET')
        with urlopen(req) as resp:
            if not (200 <= resp.status <= 299):
                raise RuntimeError("Cannot get feature index from WFS backend.")
            tree = etree.parse(resp) #type lxml._ElementTree
        if asgs_type == 'MB':
            propertyname = 'MB:MB_CODE_2016'
        elif asgs_type == 'SA1':
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif asgs_type == 'SA2':
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif asgs_type == 'SA3':
            propertyname = 'SA3:SA3_CODE_2016'
        elif asgs_type == 'SA4':
            propertyname = 'SA4:SA4_CODE_2016'
        elif asgs_type == 'STATE':
            propertyname = 'STATE:STATE_NAME_ABBREV_2016'
        else:  # australia
            propertyname = 'AUS:AUS_CODE_2016'
        items = tree.xpath('//{}/text()'.format(propertyname), namespaces=tree.getroot().nsmap)
        return items

    @classmethod
    def construct_wfs_query_for_index(cls, asgs_type, startindex, count):
        uri_template = conf.WFS_SERVICE_BASE_URI +\
                       '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
                       '&propertyName={propertyname}' \
                       '&sortBy={propertyname}&startIndex={startindex}&count={count}'
        if asgs_type == 'MB':
            service = 'MB'
            typename = 'MB:MB'
            propertyname = 'MB:MB_CODE_2016'
        elif asgs_type == 'SA1':
            service = 'SA1'
            typename = 'SA1:SA1'
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif asgs_type == 'SA2':
            service = 'SA2'
            typename = 'SA2:SA2'
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif asgs_type == 'SA3':
            service = 'SA3'
            typename = 'SA3:SA3'
            propertyname = 'SA3:SA3_CODE_2016'
        elif asgs_type == 'SA4':
            service = 'SA4'
            typename = 'SA4:SA4'
            propertyname = 'SA4:SA4_CODE_2016'
        elif asgs_type == 'STATE':
            service = 'STATE'
            typename = 'STATE:STATE'
            propertyname = 'STATE:STATE_NAME_ABBREV_2016'
        else:  # australia
            service = 'AUS'
            typename = 'AUS:AUS'
            propertyname = 'AUS:AUS_CODE_2016'

        return uri_template.format(**{
            'service': service,
            'typename': typename,
            'propertyname': propertyname,
            'startindex': startindex,
            'count': count
        })

    def get_wfs_query_for_feature_type(self):
        asgs_type = self.asgs_type
        identifier = self.id
        return self.construct_wfs_query_for_feature_type(asgs_type, identifier)

    @classmethod
    def construct_wfs_query_for_feature_type(cls, asgs_type, identifier):
        uri_template = conf.WFS_SERVICE_BASE_URI +\
                       '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
                       '&Filter=<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>{propertyname}</ogc:PropertyName>' \
                       '<ogc:Literal>{featureid}</ogc:Literal>' \
                       '</ogc:PropertyIsEqualTo></ogc:Filter>'

        if asgs_type == 'MB':
            service = 'MB'
            typename = 'MB:MB'
            propertyname = 'MB:MB_CODE_2016'
        elif asgs_type == 'SA1':
            service = 'SA1'
            typename = 'SA1:SA1'
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif asgs_type == 'SA2':
            service = 'SA2'
            typename = 'SA2:SA2'
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif asgs_type == 'SA3':
            service = 'SA3'
            typename = 'SA3:SA3'
            propertyname = 'SA3:SA3_CODE_2016'
        elif asgs_type == 'SA4':
            service = 'SA4'
            typename = 'SA4:SA4'
            propertyname = 'SA4:SA4_CODE_2016'
        elif asgs_type == 'STATE':  # state
            service = 'STATE'
            typename = 'STATE:STATE'
            propertyname = 'STATE:STATE_CODE_2016'
        else:  # australia
            service = 'AUS'
            typename = 'AUS:AUS'
            propertyname = 'AUS:AUS_CODE_2016'

        return uri_template.format(**{
            'service': service,
            'typename': typename,
            'propertyname': propertyname,
            'featureid': identifier
    })


class Req:
    def __init__(self, values):
        self.values = values


if __name__ == '__main__':
    fake_req = Req({'_view': None, '_format': None})

    afr = ASGSFeature('http://test.linked.data.gov.au/dataset/asgs/sa4/801')
    print(afr.asgs_type)
    #print(afr._get_instance_details(from_local_file=True))

    #print(AsgsFeatureRenderer.get_wfs_query_for_feature_type(
    #    'http://test.linked.data.gov.au/dataset/asgs/meshblock/80006300000'))
    # SA4
    # print(AsgsFeatureRenderer.get_wfs_query_for_feature_type(
    #     'http://test.linked.data.gov.au/dataset/asgs/sa4/801'))
