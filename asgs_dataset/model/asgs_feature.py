from datetime import datetime
from functools import lru_cache, partial

import rdflib
from flask import Response, render_template, redirect, url_for
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, XSD, OWL, Literal, BNode
from requests import Session

import asgs_dataset._config as conf
from lxml import etree
import requests
from io import StringIO, BytesIO
import os

from asgs_dataset.helpers import wfs_extract_features_as_geojson, \
    gml_extract_geom_to_geojson, gml_extract_geom_to_geosparql, RDF_a, \
    GEO, ASGS, GEO_Feature, GEO_hasGeometry, \
    wfs_extract_features_with_rdf_converter, calculate_bbox
from asgs_dataset.model import ASGSModel
from asgs_dataset.model.lookups import *

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

sa1_tag_map = {
    "{WFS}SA1_MAINCODE_2016": 'code',
    "{WFS}SA2_MAINCODE_2016": "sa2",
    "{WFS}STATE_CODE_2016": "state",
    "{WFS}SA1_7DIGITCODE_2016": "seven_code",
}

sa2_tag_map = {
    "{WFS}SA2_MAINCODE_2016": 'code',
    "{WFS}SA2_NAME_2016": 'name',
    "{WFS}SA3_CODE_2016": "sa3",
    "{WFS}STATE_CODE_2016": "state",
}

sa3_tag_map = {
    "{WFS}SA3_CODE_2016": 'code',
    "{WFS}SA3_NAME_2016": 'name',
    "{WFS}SA4_CODE_2016": "sa4",
    "{WFS}STATE_CODE_2016": "state",
}

sa4_tag_map = {
    "{WFS}SA4_CODE_2016": 'code',
    "{WFS}SA4_NAME_2016": 'name',
    "{WFS}GCCSA_CODE_2016": "gccsa",
    "{WFS}STATE_CODE_2016": "state",
}

state_tag_map = {
    "{WFS}STATE_CODE_2016": 'code',
    "{WFS}STATE_NAME_2016": 'name',
    "{WFS}STATE_NAME_ABBREV_2016": 'name_abbrev'
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
        'shape': gml_extract_geom_to_geosparql
    }
    to_float = ('shape_length', 'shape_area', 'albers_area')
    to_int = ('object_id', 'category', 'state')
    is_geom = ('shape',)
    predicate_map = {
        #'nextdownid': HYF_lowerCatchment
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
                val = Literal(int(val))
            else:
                if not isinstance(val, (URIRef, Literal, BNode)):
                    val = Literal(str(val))
            if var in is_geom:
                triples.add((feature_uri, GEO_hasGeometry, val))
            elif var in predicate_map.keys():
                predicate = predicate_map[var]
                triples.add((feature_uri, predicate, val))
            else:
                dummy_prop = URIRef("{}/{}".format("WFS", var))
                triples.add((feature_uri, dummy_prop, val))
        features_list.append(feature_uri)
    return triples, feature_nodes

def extract_asgs_features_as_geojson(asgs_type, tree):
    geojson_features = wfs_extract_features_as_geojson(
        tree, 'WFS', asgs_type,
        partial(asgs_features_geojson_converter, asgs_type))
    return geojson_features

def extract_asgs_features_as_geosparql(asgs_type, canonical_uri, tree):
    g = rdflib.Graph()
    g.bind('asgs', ASGS)
    g.bind('geo', GEO)
    triples, features = wfs_extract_features_with_rdf_converter(
        tree, 'WFS', asgs_type,
        partial(asgs_features_geosparql_converter, asgs_type, canonical_uri))
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
    if tree is None:
        wfs_uri = ASGSFeature.construct_wfs_query_for_feature_type(
            asgs_type, identifier)
        session = retrieve_asgs_feature.session
        if session is None:
            session = retrieve_asgs_feature.session = Session()
        try:
            r = session.get(wfs_uri)
        except Exception as e:
            raise e
        tree = etree.parse(BytesIO(r.content), parser=parser)
    return tree
retrieve_asgs_feature.session = None


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
            return url_for("controller.redirect_aus", aus=instance_id)
        return url_for("controller.object", uri=instance_uri)

    def __init__(self, uri):
        super(ASGSFeature, self).__init__()
        # split ID out of URI for all ASGS Features
        self.uri = uri
        self.id = uri.split('/')[-1]
        self._assign_asgs_type()
        if self.asgs_type == "STATE":
            # State can sometimes be called by the code rather than the name
            try:
                state_int = int(self.id)
                if 9 >= state_int >= 1:
                    self.id = STATES[state_int]
            except ValueError:
                pass
        feature_xml_tree = retrieve_asgs_feature(self.asgs_type, self.id)
        self.xml_tree = feature_xml_tree
        wfs_features = extract_asgs_features_as_geojson(
            self.asgs_type, feature_xml_tree)
        asgs_feature = wfs_features['features'][0]
        self.geometry = asgs_feature['geometry']
        self.properties = asgs_feature['properties']

    @classmethod
    def determine_asgs_type(cls, instance_uri):
        if '/meshblock/' in instance_uri:
            return 'MB'
        elif '/sa1/' in instance_uri:
            return 'SA1'
        elif '/sa2/' in instance_uri:
            return 'SA2'
        elif '/sa3/' in instance_uri:
            return 'SA3'
        elif '/sa4/' in instance_uri:
            return 'SA4'
        elif '/state/' in instance_uri:
            return 'STATE'
        else:  # australia
            return 'AUS'

    def _assign_asgs_type(self):
        self.asgs_type = self.determine_asgs_type(self.uri)

    def as_geosparql(self):
        return extract_asgs_features_as_geosparql(
            self.asgs_type, self.uri, self.xml_tree)

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

    # def _get_instance_details(self, from_local_file=True):
    #
    #     def _get_mb_details(root):
    #         return {
    #             'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
    #             'object_id': root.xpath('//MB:MB/MB:OBJECTID', namespaces={'MB': 'WFS'})[0].text,
    #             'category': root.xpath('//MB:MB/MB:MB_CATEGORY_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'category_name': root.xpath('//MB:MB/MB:MB_CATEGORY_NAME_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'code': root.xpath('//MB:MB/MB:MB_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'albers_area': root.xpath('//MB:MB/MB:AREA_ALBERS_SQKM', namespaces={'MB': 'WFS'})[0].text,
    #             'sa1': root.xpath('//MB:MB/MB:SA1_MAINCODE_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'state': int(root.xpath('//MB:MB/MB:STATE_CODE_2016', namespaces={'MB': 'WFS'})[0].text),
    #             'dzn': root.xpath('//MB:MB/MB:DZN_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'ssc': root.xpath('//MB:MB/MB:SSC_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'nrmr': root.xpath('//MB:MB/MB:NRMR_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'add': root.xpath('//MB:MB/MB:ADD_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
    #             'shape_length': root.xpath('//MB:MB/MB:Shape_Length', namespaces={'MB': 'WFS'})[0].text,
    #             'shape_area': root.xpath('//MB:MB/MB:Shape_Area', namespaces={'MB': 'WFS'})[0].text
    #         }
    #
    #     def _get_sa1_details(root):
    #         return {
    #             'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
    #             'object_id': root.xpath('//SA1:OBJECTID', namespaces={'SA1': 'WFS'})[0].text,
    #             'albers_area': root.xpath('//SA1:AREA_ALBERS_SQKM', namespaces={'SA1': 'WFS'})[0].text,
    #             'sa2': root.xpath('//SA1:SA2_MAINCODE_2016', namespaces={'SA1': 'WFS'})[0].text,
    #             'code': root.xpath('//SA1:SA1_MAINCODE_2016', namespaces={'SA1': 'WFS'})[0].text,
    #             'seven_code': root.xpath('//SA1:SA1_7DIGITCODE_2016', namespaces={'SA1': 'WFS'})[0].text,
    #             'state': int(root.xpath('//SA1:STATE_CODE_2016', namespaces={'SA1': 'WFS'})[0].text),
    #             'shape_length': root.xpath('//SA1:Shape_Length', namespaces={'SA1': 'WFS'})[0].text,
    #             'shape_area': root.xpath('//SA1:Shape_Area', namespaces={'SA1': 'WFS'})[0].text
    #         }
    #
    #     def _get_sa2_details(root):
    #         return {
    #             'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
    #             'object_id': root.xpath('//SA2:OBJECTID', namespaces={'SA2': 'WFS'})[0].text,
    #             'albers_area': root.xpath('//SA2:AREA_ALBERS_SQKM', namespaces={'SA2': 'WFS'})[0].text,
    #             'sa3': root.xpath('//SA2:SA3_CODE_2016', namespaces={'SA2': 'WFS'})[0].text,
    #             'code': root.xpath('//SA2:SA2_MAINCODE_2016', namespaces={'SA2': 'WFS'})[0].text,
    #             'name': root.xpath('//SA2:SA2_NAME_2016', namespaces={'SA2': 'WFS'})[0].text,
    #             'state': int(root.xpath('//SA2:STATE_CODE_2016', namespaces={'SA2': 'WFS'})[0].text),
    #             'shape_length': root.xpath('//SA2:Shape_Length', namespaces={'SA2': 'WFS'})[0].text,
    #             'shape_area': root.xpath('//SA2:Shape_Area', namespaces={'SA2': 'WFS'})[0].text
    #         }
    #
    #     def _get_sa3_details(root):
    #         return {
    #             'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
    #             'object_id': root.xpath('//SA3:SA3/SA3:OBJECTID', namespaces={'SA3': 'WFS'})[0].text,
    #             'name': root.xpath('//SA3:SA3/SA3:SA3_NAME_2016', namespaces={'SA3': 'WFS'})[0].text,
    #             'albers_area': root.xpath('//SA3:SA3/SA3:AREA_ALBERS_SQKM', namespaces={'SA3': 'WFS'})[0].text,
    #             'code': root.xpath('//SA3:SA3/SA3:SA3_CODE_2016', namespaces={'SA3': 'WFS'})[0].text,
    #             'sa4': root.xpath('//SA3:SA3/SA3:SA4_CODE_2016', namespaces={'SA3': 'WFS'})[0].text,
    #             'state': int(root.xpath('//SA3:SA3/SA3:STATE_CODE_2016', namespaces={'SA3': 'WFS'})[0].text),
    #             'shape_length': root.xpath('//SA3:SA3/SA3:Shape_Length', namespaces={'SA3': 'WFS'})[0].text,
    #             'shape_area': root.xpath('//SA3:SA3/SA3:Shape_Area', namespaces={'SA3': 'WFS'})[0].text
    #         }
    #
    #     def _get_sa4_details(root):
    #         return {
    #             'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
    #             'object_id': root.xpath('//SA4:OBJECTID', namespaces={'SA4': 'WFS'})[0].text,
    #             'name': root.xpath('//SA4:SA4_NAME_2016', namespaces={'SA4': 'WFS'})[0].text,
    #             'albers_area': root.xpath('//SA4:AREA_ALBERS_SQKM', namespaces={'SA4': 'WFS'})[0].text,
    #             'code': int(root.xpath('//SA4:SA4_CODE_2016', namespaces={'SA4': 'WFS'})[0].text),
    #             'state': int(root.xpath('//SA4:STATE_CODE_2016', namespaces={'SA4': 'WFS'})[0].text),
    #             'shape_length': root.xpath('//SA4:Shape_Length', namespaces={'SA4': 'WFS'})[0].text,
    #             'shape_area': root.xpath('//SA4:Shape_Area', namespaces={'SA4': 'WFS'})[0].text
    #         }
    #
    #     def _get_state_details(root):
    #         return {
    #             'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
    #             'object_id': root.xpath('//STATE:OBJECTID', namespaces={'STATE': 'WFS'})[0].text,
    #             'name': root.xpath('//STATE:STATE_NAME_2016', namespaces={'STATE': 'WFS'})[0].text,
    #             'name_abbrev': root.xpath('//STATE:STATE_NAME_ABBREV_2016', namespaces={'STATE': 'WFS'})[0].text,
    #             'albers_area': root.xpath('//STATE:AREA_ALBERS_SQKM', namespaces={'STATE': 'WFS'})[0].text,
    #             'code': int(root.xpath('//STATE:STATE_CODE_2016', namespaces={'STATE': 'WFS'})[0].text),
    #             'shape_length': root.xpath('//STATE:Shape_Length', namespaces={'STATE': 'WFS'})[0].text,
    #             'shape_area': root.xpath('//STATE:Shape_Area', namespaces={'STATE': 'WFS'})[0].text
    #         }
    #     def _get_aus_details(root):
    #         return {
    #             'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
    #             'object_id': root.xpath('//AUS:OBJECTID', namespaces={'AUS': 'WFS'})[0].text,
    #             'name': root.xpath('//AUS:AUS_NAME_2016', namespaces={'AUS': 'WFS'})[0].text,
    #             'code': int(root.xpath('//AUS:AUS_CODE_2016', namespaces={'AUS': 'WFS'})[0].text),
    #             'shape_length': root.xpath('//AUS:Shape_Length', namespaces={'AUS': 'WFS'})[0].text,
    #             'shape_area': root.xpath('//AUS:Shape_Area', namespaces={'AUS': 'WFS'})[0].text
    #         }
    #     # handle any connection exceptions
    #     try:
    #         root = None
    #         if from_local_file:  # a stub to use a local file for testing
    #             xml_file = os.path.join(
    #                 os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
    #                 'test',
    #                 self.asgs_type + '_' + self.id + '.xml')
    #             try:
    #                 if self.asgs_type == "STATE" or self.asgs_type == "AUS":
    #                     parser = etree.XMLParser(recover=True, huge_tree=True)
    #                 else:
    #                     parser = etree.XMLParser(recover=True)
    #                 root = etree.parse(xml_file, parser=parser)
    #             except (FileNotFoundError, OSError):
    #                 root = None
    #             except Exception as e:
    #                 print(e)
    #         if root is None:
    #             wfs_uri = self.get_wfs_query_for_feature_type()
    #             r = requests.get(wfs_uri)
    #
    #             # check we have a valid result with an XPath to get the posList (polygon coordinates)
    #             root = etree.parse(StringIO(r.text))
    #         try:
    #             coords = root.xpath('//gml:posList', namespaces={'gml': 'http://www.opengis.net/gml/3.2'})
    #         except IndexError as e:
    #             return False, 'No Mesh Block with that ID was found'
    #
    #         coords_wkt = ''
    #         c = coords[0].text.strip().split(' ')  # must strip to remove leading ' '
    #
    #         for i in range(0, len(c), 2):
    #             coords_wkt += c[i] + ',' + c[i + 1] + ' '
    #
    #         if self.asgs_type == 'MB':
    #             d = _get_mb_details(root)
    #         elif self.asgs_type == 'SA1':
    #             d = _get_sa1_details(root)
    #         elif self.asgs_type == 'SA2':
    #             d = _get_sa2_details(root)
    #         elif self.asgs_type == 'SA3':
    #             d = _get_sa3_details(root)
    #         elif self.asgs_type == 'SA4':
    #             d = _get_sa4_details(root)
    #         elif self.asgs_type == 'STATE':
    #             d = _get_state_details(root)
    #         elif self.asgs_type == 'AUS':
    #             d = _get_aus_details(root)
    #         else:
    #             raise RuntimeError()
    #
    #         return True, d
    #
    #     except Exception as e:
    #         return False, str(e)

    def _get_instance_rdf(self, profile='asgs'):  # fixed to asgs profile for now
        deets = self.properties
        if profile == 'asgs' or profile == 'geosparql':
            g = self.as_geosparql()
            # ID & definition of the MB
            mb = URIRef(self.uri)
            if self.asgs_type == "MB":
                g.add((mb, RDF_a, ASGS.MeshBlock))
                # SA1 - 2nd level register
                g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/dataset/asgs/sa1/' + deets['sa1'])))
                # TODO: Do category and category_name for MB
            elif self.asgs_type == "SA1":
                g.add((mb, RDF_a, ASGS.SA1))
                g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/dataset/asgs/sa2/' + deets['sa2'])))
            elif self.asgs_type == "SA2":
                g.add((mb, RDF_a, ASGS.SA2))
                g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/dataset/asgs/sa3/' + deets['sa3'])))
            elif self.asgs_type == "SA3":
                g.add((mb, RDF_a, ASGS.SA3))
                g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/dataset/asgs/sa4/' + deets['sa4'])))
            elif self.asgs_type == "SA4":
                g.add((mb, RDF_a, ASGS.SA4))
            elif self.asgs_type == "STATE":
                g.add((mb, RDF_a, ASGS.State))
            else:
                g.add((mb, RDF_a, ASGS.Australia))
            if self.asgs_type != "AUS" and self.asgs_type != "STATE":
                # State - top-level register
                g.add((mb, GEO.sfWithin, URIRef(
                    'http://linked.data.gov.au/state/' + STATES[
                        deets['state']])))
                # TODO: add hasState to ASGS ont as a subProperty of sfWithin wth fixed range value being an Aust state individual
                g.add((mb, ASGS.hasState, URIRef(
                    'http://linked.data.gov.au/state/' + STATES[
                        deets['state']])))

            # area
            # TODO: check multiplier on m^2 or km^2
            QUDT = Namespace('http://qudt.org/schema/qudt/')
            g.bind('qudt', QUDT)

            area = BNode()  # must be a qudt:QuantityValue as per QUDT
            # qudt:Quantity qudt:quantityValue qudt:QuantityValue
            #               qudt:QuantityKind
            # qudt:QuantityKind qudt:symbol (max 1) xsd:string ($\\ohm$) -> owl:DatatypeProperty , qudt:latexMathString
            # qudt:QuantityKind qudt:abbreviation (max 1) xsd:string (ohm) -> owl:DatatypeProperty
            g.add((mb, ASGS.hasArea, area))
            g.add((area, QUDT.numericValue, Literal(deets['shape_area'], datatype=XSD.decimal)))
            g.add((area, QUDT.unit, QUDT.SquareMeter))

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
        return conf.MESHBLOCK_COUNT

    @staticmethod
    def total_sa1s():
        return conf.SA1_COUNT

    @staticmethod
    def total_sa2s():
        return conf.SA2_COUNT

    @staticmethod
    def total_sa3s():
        return conf.SA3_COUNT

    @staticmethod
    def total_sa4s():
        return conf.SA4_COUNT  # return 49

    @staticmethod
    def total_states():
        return 9

    @classmethod
    def get_feature_index(cls, asgs_type, startindex, count):
        url = cls.construct_wfs_query_for_index(asgs_type, startindex, count)
        resp = requests.get(url)
        tree = etree.parse(BytesIO(resp.content)) #type lxml._ElementTree
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
            propertyname = 'STATE:STATE_NAME_ABBREV_2016'
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
