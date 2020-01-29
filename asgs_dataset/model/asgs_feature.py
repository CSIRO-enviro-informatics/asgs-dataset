from collections import namedtuple
from datetime import datetime
from functools import lru_cache, partial
from urllib.error import HTTPError
from urllib.parse import urlencode
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
    ASGS_ID, GEO_within, GEO_contains, AsgsWfsType, load_gz_pickle, FakeXMLElement
from asgs_dataset.model import ASGSModel, NotFoundError

MESHBLOCK_COUNT = 358009
SA1_COUNT = 57490
SA2_COUNT = 2292
SA3_COUNT = 340
SA4_COUNT = 89
GCCSA_COUNT = 17
SUA_COUNT = 110
RA_COUNT = 53
UCL_COUNT = 1853
SOSR_COUNT = 89
SOS_COUNT = 52
ILOC_COUNT = 1097
IARE_COUNT = 412
IREG_COUNT = 40


INVERSE_TOKEN = object()
# Inverse token is used when a relationship need to be expressed in an inverse way, eg:
# Instead of MB1,sfWithin,SA1 we want it expressed as SA1,sfContains,MB1

LOCAL_LOOKUP_TOKEN = object()
# Used when the data property on the WFS is known missing or unreliable
# Forces the mapper to use a local lookup dict to get the value

IGNORE_TOKEN = object()
# Used when we want to acknowledge a data property's existence but not use it.

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
    "AUS": "asgs16_aus/",
    "GCCSA": "asgs16_gccsa/",
    "SUA": "asgs16_sua/",
    "RA": "asgs16_ra/",
    "UCL": "asgs16_ucl/",
    "SOSR": "asgs16_sosr/",
    "SOS": "asgs16_sos/",
    "ILOC": "asgs16_iloc/",
    "IARE": "asgs16_iare/",
    "IREG": "asgs16_ireg/",
}

feature_identification_types = {
    "MB": ASGS_ID.term("mbCode2016"),
    "SA1": ASGS_ID.term("sa1Maincode2016"),
    "SA2": ASGS_ID.term("sa2Maincode2016"),
    "SA3": ASGS_ID.term("sa3Code2016"),
    "SA4": ASGS_ID.term("sa4Code2016"),
    "STATE": ASGS_ID.term("stateCode2016"),
    "AUS": ASGS_ID.term("ausCode2016"),
    "GCCSA": ASGS_ID.term("gccsaCode2016"),
    "SUA": ASGS_ID.term("suaCode2016"),
    "RA": ASGS_ID.term("raCode2016"),
    "UCL": ASGS_ID.term("uclCode2016"),
    "SOSR": ASGS_ID.term("sosrCode2016"),
    "SOS": ASGS_ID.term("sosCode2016"),
    "ILOC": ASGS_ID.term("ilocCode2016"),
    "IARE": ASGS_ID.term("iareCode2016"),
    "IREG": ASGS_ID.term("iregCode2016"),
}

ASGS_WFS_MB = AsgsWfsType('MB', 'MB:MB', 'MB:MB_CODE_2016')  # Meshblock
ASGS_WFS_SA1 = AsgsWfsType('SA1', 'SA1:SA1', 'SA1:SA1_MAINCODE_2016')  # StatisticalAreaLevel1
ASGS_WFS_SA2 = AsgsWfsType('SA2', 'SA2:SA2', 'SA2:SA2_MAINCODE_2016')  # StatisticalAreaLevel2
ASGS_WFS_SA3 = AsgsWfsType('SA3', 'SA3:SA3', 'SA3:SA3_CODE_2016')  # StatisticalAreaLevel3
ASGS_WFS_SA4 = AsgsWfsType('SA4', 'SA4:SA4', 'SA4:SA4_CODE_2016')  # StatisticalAreaLevel4
ASGS_WFS_STATE = AsgsWfsType('STATE', 'STATE:STATE', 'STATE:STATE_NAME_ABBREV_2016')  # States (by name abbrev)
#ASGS_WFS_STATE = AsgsWfsType('STATE', 'STATE:STATE', 'STATE:STATE_CODE_2016')  # States (by 1-digit code)
ASGS_WFS_AUS = AsgsWfsType('AUS', 'AUS:AUS', 'AUS:AUS_CODE_2016')  # Australia
ASGS_WFS_GCCSA = AsgsWfsType('GCCSA', 'GCCSA:GCCSA', 'GCCSA:GCCSA_CODE_2016')  # GreaterCapitalCityStatisticalArea
ASGS_WFS_SUA = AsgsWfsType('SUA', 'SUA:SUA', 'SUA:SUA_CODE_2016')  # SignificantUrbanArea
ASGS_WFS_RA = AsgsWfsType('RA', 'RA:RA', 'RA:RA_CODE_2016')  # RemotenessArea
ASGS_WFS_UCL = AsgsWfsType('UCL', 'UCL:UCL', 'UCL:UCL_CODE_2016')  # UrbanCentresAndLocalities
ASGS_WFS_SOSR = AsgsWfsType('SOSR', 'SOSR:SOSR', 'SOSR:SOSR_CODE_2016')  # SectionOfStateRange
ASGS_WFS_SOS = AsgsWfsType('SOS', 'SOS:SOS', 'SOS:SOS_CODE_2016')  # SectionOfState
ASGS_WFS_ILOC = AsgsWfsType('ILOC', 'ILOC:ILOC', 'ILOC:ILOC_CODE_2016')  # IndigenousLocation
ASGS_WFS_IARE = AsgsWfsType('IARE', 'IARE:IARE', 'IARE:IARE_CODE_2016')  # IndigenousArea
ASGS_WFS_IREG = AsgsWfsType('IREG', 'IREG:IREG', 'IREG:IREG_CODE_2016')  # IndigenousRegion

ASGS_WFS_LOOKUP = {
    "MB": ASGS_WFS_MB,  # Meshblock
    "SA1": ASGS_WFS_SA1,  # StatisticalAreaLevel1
    "SA2": ASGS_WFS_SA2,  # StatisticalAreaLevel2
    "SA3": ASGS_WFS_SA3,  # StatisticalAreaLevel3
    "SA4": ASGS_WFS_SA4,  # StatisticalAreaLevel4
    "STATE": ASGS_WFS_STATE,  # States
    "AUS": ASGS_WFS_AUS,  # Australia
    "GCCSA": ASGS_WFS_GCCSA,  # GreaterCapitalCityStatisticalArea
    "SUA": ASGS_WFS_SUA,  # SignificantUrbanArea
    "RA": ASGS_WFS_RA,  # RemotenessArea
    "UCL": ASGS_WFS_UCL,  # UrbanCentresAndLocalities
    "SOSR": ASGS_WFS_SOSR,  # SectionOfStateRange
    "SOS": ASGS_WFS_SOS,  # SectionOfState
    "ILOC": ASGS_WFS_ILOC,  # IndigenousLocation
    "IARE": ASGS_WFS_IARE,  # IndigenousArea
    "IREG": ASGS_WFS_IREG,  # IndigenousRegion
}

LOCAL_DATA_VAL_LOOKUPS = {
    **load_gz_pickle("sa1_to_iloc"),
    **load_gz_pickle("sa1_to_ucl"),
    **load_gz_pickle("sa1_to_ra"),
    **load_gz_pickle("sa2_to_sua"),
}


common_tag_map = {
    "{WFS}OBJECTID": "object_id",
    "{WFS}Shape_Length": 'shape_length',
    "{WFS}Shape_Area": 'shape_area',
    "{WFS}Shape": 'shape',
    "{WFS}SHAPE": 'shape',
    "{WFS}SHAPE_Length": 'shape_length',
    "{WFS}SHAPE_Area": 'shape_area',
}

mb_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
    "{WFS}MB_CODE_2016": 'code',
    "{WFS}MB_CATEGORY_CODE_2016": "category_code",
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
    'category_code': IGNORE_TOKEN,
    'category_name': [ASGS.category],
    'sa1': INVERSE_TOKEN,
    'state': INVERSE_TOKEN,
    'dzn': INVERSE_TOKEN,
    'ssc': INVERSE_TOKEN,
    'nrmr': INVERSE_TOKEN,
    'add': IGNORE_TOKEN,
}
mb_predicate_map_loci = {
    'code': [DCTERMS.identifier],
    'category_name': IGNORE_TOKEN,
    'category_code': [DCTERMS.type],
    'sa1': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
    'dzn': [GEO_within, INVERSE_TOKEN],
    'ssc': [GEO_within, INVERSE_TOKEN],
    'nrmr': [GEO_within, INVERSE_TOKEN],
    'add': IGNORE_TOKEN,
}

sa1_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
    "{WFS}SA1_MAINCODE_2016": 'code',
    "{WFS}SA2_MAINCODE_2016": "sa2",
    "{WFS}STATE_CODE_2016": "state",
    "{WFS}SA1_7DIGITCODE_2016": "seven_code",
    "{WFS}RA_CODE_2016": (LOCAL_LOOKUP_TOKEN, "ra"),
    "{WFS}UCL_CODE_2016": (LOCAL_LOOKUP_TOKEN, "ucl"),
    "{WFS}ILOC_CODE_2016": (LOCAL_LOOKUP_TOKEN, "iloc"),
}
sa1_predicate_map_asgs = {
    'code': [ASGS.sa1Maincode2016, ASGS.statisticalArea1Sa111DigitCode],
    'seven_code': IGNORE_TOKEN,
    'sa2': INVERSE_TOKEN,
    'state': INVERSE_TOKEN,
    'ra': INVERSE_TOKEN,
    'ucl': INVERSE_TOKEN,
    'iloc': INVERSE_TOKEN
}
sa1_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.statisticalArea1Sa111DigitCode],
    'seven_code': IGNORE_TOKEN,
    'sa2': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
    'ra': [GEO_within, INVERSE_TOKEN],
    'ucl': [GEO_within, INVERSE_TOKEN],
    'iloc': [GEO_within, INVERSE_TOKEN],
}

sa2_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
    "{WFS}SA2_MAINCODE_2016": 'code',
    "{WFS}SA2_NAME_2016": 'name',
    "{WFS}SA3_CODE_2016": "sa3",
    "{WFS}STATE_CODE_2016": "state",
    "{WFS}SUA_CODE_2016": (LOCAL_LOOKUP_TOKEN, "sua"),
}
sa2_predicate_map_asgs = {
    'code': [ASGS.sa2Maincode2016, ASGS.statisticalArea2Sa29DigitCode],
    'name': [ASGS.sa2Name2016],
    'sa3': INVERSE_TOKEN,
    'state': INVERSE_TOKEN,
    'sua': INVERSE_TOKEN,
}
sa2_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.statisticalArea2Sa29DigitCode],
    'name': [DCTERMS.title],
    'sa3': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
    'sua': [GEO_within, INVERSE_TOKEN],
}

sa3_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
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
    'name': [DCTERMS.title],
    'sa4': [GEO_within, INVERSE_TOKEN],
    'state': [GEO_within, INVERSE_TOKEN],
}

sa4_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
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
    'name': [DCTERMS.title],
    'state': [GEO_within, INVERSE_TOKEN],
    'gccsa': [GEO_within, INVERSE_TOKEN],
}
gccsa_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
    "{WFS}GCCSA_CODE_2016": 'code',
    "{WFS}GCCSA_NAME_2016": 'name',
    "{WFS}STATE_CODE_2016": "state",
}
gccsa_predicate_map_asgs = {
    'code': [ASGS.gccsaCode2016, ASGS.greaterCapitalCityStatisticalAreasGccsa5CharacterAlphanumericCode],
    'name': [ASGS.gccsaName2016],
    'state': INVERSE_TOKEN,
}
gccsa_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.greaterCapitalCityStatisticalAreasGccsa5CharacterAlphanumericCode],
    'name': [DCTERMS.title],
    'state': [GEO_within, INVERSE_TOKEN],
}
ra_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
    "{WFS}RA_CODE_2016": 'code',
    "{WFS}RA_NAME_2016": 'name',
    "{WFS}STATE_CODE_2016": "state",
}
ra_predicate_map_asgs = {
    'code': [ASGS.raCode2016],
    'name': [ASGS.raName2016],
    'state': INVERSE_TOKEN,
}
ra_predicate_map_loci = {
    'code': [DCTERMS.identifier],
    'name': [DCTERMS.title],
    'state': [GEO_within, INVERSE_TOKEN],
}
iloc_tag_map = {
    "{WFS}ILOC_CODE_2016": 'code',
    "{WFS}ILOC_NAME_2016": 'name',
}
iloc_predicate_map_asgs = {
    'code': [ASGS.ilocCode2016],
    'name': [ASGS.ilocName2016],
}
iloc_predicate_map_loci = {
    'code': [DCTERMS.identifier],
    'name': [DCTERMS.title],
}

ireg_tag_map = {
    "{WFS}IREG_CODE_2016": 'code',
    "{WFS}IREG_NAME_2016": 'name',
}
ireg_predicate_map_asgs = {
    'code': [ASGS.iregCode2016, ASGS.indigenousRegions3DigitCode],
    'name': [ASGS.iregName2016],
}
ireg_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.indigenousRegions3DigitCode],
    'name': [DCTERMS.title],
}

iare_tag_map = {
    "{WFS}IARE_CODE_2016": 'code',
    "{WFS}IARE_NAME_2016": 'name',
}
iare_predicate_map_asgs = {
    'code': [ASGS.iareCode2016, ASGS.indigenousAreas6DigitCode],
    'name': [ASGS.iareName2016],
}
iare_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.indigenousAreas6DigitCode],
    'name': [DCTERMS.title],
}

ucl_tag_map = {
    "{WFS}UCL_CODE_2016": 'code',
}
ucl_predicate_map_asgs = {
    'code': [ASGS.uclCode2016],
}
ucl_predicate_map_loci = {
    'code': [DCTERMS.identifier],
}

sosr_tag_map = {
    "{WFS}SOSR_CODE_2016": 'code',
}
sosr_predicate_map_asgs = {
    'code': [ASGS.sosrCode2016, ASGS.sectionOfStateRange3DigitCode],
}
sosr_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.sectionOfStateRange3DigitCode],
}

sos_tag_map = {
    "{WFS}SOS_CODE_2016": 'code',
}
sos_predicate_map_asgs = {
    'code': [ASGS.sosCode2016, ASGS.sectionOfState2DigitCode],
}
sos_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.sectionOfState2DigitCode],
}

sua_tag_map = {
    "{WFS}SUA_CODE_2016": 'code',
}
sua_predicate_map_asgs = {
    'code': [ASGS.suaCode2016],
}
sua_predicate_map_loci = {
    'code': [DCTERMS.identifier],
}

state_tag_map = {
    "{WFS}AREA_ALBERS_SQKM": 'albers_area',
    "{WFS}STATE_CODE_2016": 'code',
    "{WFS}STATE_NAME_2016": 'name',
    "{WFS}STATE_NAME_ABBREV_2016": 'name_abbrev'
}
state_predicate_map_asgs = {
    'code': [ASGS.stateCode2016, ASGS.stateOrTerritory1DigitCode],
    'name': [ASGS.stateName2016],
    'name_abbrev': [ASGS.label]
}
state_predicate_map_loci = {
    'code': [DCTERMS.identifier, ASGS.stateOrTerritory1DigitCode],
    'name': [DCTERMS.title],
    'name_abbrev': [RDFS.label]
}

australia_tag_map = {
    "{WFS}AUS_CODE_2016": 'code',
    "{WFS}AUS_NAME_2016": 'name',
}
australia_predicate_map_asgs = {
    'code': [ASGS.ausCode2016],
    'name': [ASGS.ausName2016],
}
australia_predicate_map_loci = {
    'code': [DCTERMS.identifier],
    'name': [DCTERMS.title],
}

common_predicate_map_asgs = {
    'shape_area': [GEOX.hasAreaM2],
    'albers_area': [GEOX.hasAreaM2],
}

tag_map_lookup = {
    "AUS": {**common_tag_map, **australia_tag_map},  # Australia
    "MB": {**common_tag_map, **mb_tag_map},  # Meshblock
    "SA1": {**common_tag_map, **sa1_tag_map},  # StatisticalAreaLevel1
    "SA2": {**common_tag_map, **sa2_tag_map},  # StatisticalAreaLevel2
    "SA3": {**common_tag_map, **sa3_tag_map},  # StatisticalAreaLevel3
    "SA4": {**common_tag_map, **sa4_tag_map},  # StatisticalAreaLevel4
    "STATE": {**common_tag_map, **state_tag_map},  # State
    "GCCSA": {**common_tag_map, **gccsa_tag_map},  # GreaterCapitalCityStatisticalArea
    "SUA": {**common_tag_map, **sua_tag_map},  # SignificantUrbanArea
    "RA": {**common_tag_map, **ra_tag_map},  # RemotenessArea
    "UCL": {**common_tag_map, **ucl_tag_map},  # UrbanCentresAndLocalities
    "SOSR": {**common_tag_map, **sosr_tag_map},  # SectionOfStateRange
    "SOS": {**common_tag_map, **sos_tag_map},  # SectionOfState
    "ILOC": {**common_tag_map, **iloc_tag_map},  # IndigenousLocation
    "IARE": {**common_tag_map, **iare_tag_map},  # IndigenousArea
    "IREG": {**common_tag_map, **ireg_tag_map},  # IndigenousRegion
}
predicate_map_lookup = {
    "geosparql": {
        "AUS": {**common_predicate_map_asgs, **australia_predicate_map_asgs},  # Australia
        "MB": {**common_predicate_map_asgs, **mb_predicate_map_asgs},  # Meshblock
        "SA1": {**common_predicate_map_asgs, **sa1_predicate_map_asgs},  # StatisticalAreaLevel1
        "SA2": {**common_predicate_map_asgs, **sa2_predicate_map_asgs},  # StatisticalAreaLevel2
        "SA3": {**common_predicate_map_asgs, **sa3_predicate_map_asgs},  # StatisticalAreaLevel3
        "SA4": {**common_predicate_map_asgs, **sa4_predicate_map_asgs},  # StatisticalAreaLevel4
        "STATE": {**common_predicate_map_asgs, **state_predicate_map_asgs},  # State
        "GCCSA": {**common_predicate_map_asgs, **gccsa_predicate_map_asgs},  # GreaterCapitalCityStatisticalArea
        "SUA": {**common_predicate_map_asgs, **sua_predicate_map_asgs},  # SignificantUrbanArea
        "RA": {**common_predicate_map_asgs, **ra_predicate_map_asgs},  # RemotenessArea
        "UCL": {**common_predicate_map_asgs, **ucl_predicate_map_asgs},  # UrbanCentresAndLocalities
        "SOSR": {**common_predicate_map_asgs, **sosr_predicate_map_asgs},  # SectionOfStateRange
        "SOS": {**common_predicate_map_asgs, **sos_predicate_map_asgs},  # SectionOfState
        "ILOC": {**common_predicate_map_asgs, **iloc_predicate_map_asgs},  # IndigenousLocation
        "IARE": {**common_predicate_map_asgs, **iare_predicate_map_asgs},  # IndigenousArea
        "IREG": {**common_predicate_map_asgs, **ireg_predicate_map_asgs},  # IndigenousRegion
    },
    "loci": {
        "AUS": {**common_predicate_map_asgs, **australia_predicate_map_loci},  # Australia
        "MB": {**common_predicate_map_asgs, **mb_predicate_map_loci},  # Meshblock
        "SA1": {**common_predicate_map_asgs, **sa1_predicate_map_loci},  # StatisticalAreaLevel1
        "SA2": {**common_predicate_map_asgs, **sa2_predicate_map_loci},  # StatisticalAreaLevel2
        "SA3": {**common_predicate_map_asgs, **sa3_predicate_map_loci},  # StatisticalAreaLevel3
        "SA4": {**common_predicate_map_asgs, **sa4_predicate_map_loci},  # StatisticalAreaLevel4
        "STATE": {**common_predicate_map_asgs, **state_predicate_map_loci},  # State
        "GCCSA": {**common_predicate_map_asgs, **gccsa_predicate_map_loci},  # GreaterCapitalCityStatisticalArea
        "SUA": {**common_predicate_map_asgs, **sua_predicate_map_loci},  # SignificantUrbanArea
        "RA": {**common_predicate_map_asgs, **ra_predicate_map_loci},  # RemotenessArea
        "UCL": {**common_predicate_map_asgs, **ucl_predicate_map_loci},  # UrbanCentresAndLocalities
        "SOSR": {**common_predicate_map_asgs, **sosr_predicate_map_loci},  # SectionOfStateRange
        "SOS": {**common_predicate_map_asgs, **sos_predicate_map_loci},  # SectionOfState
        "ILOC": {**common_predicate_map_asgs, **iloc_predicate_map_loci},  # IndigenousLocation
        "IARE": {**common_predicate_map_asgs, **iare_predicate_map_loci},  # IndigenousArea
        "IREG": {**common_predicate_map_asgs, **ireg_predicate_map_loci},  # IndigenousRegion
    }
}
predicate_map_lookup['asgs'] = predicate_map_lookup['geosparql']

state_id_map = {
    1: "NSW",
    2: "VIC",
    3: "QLD",
    4: "SA",
    5: "WA",
    6: "TAS",
    7: "NT",
    8: "ACT",
    9: "OT"
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

    tag_map = tag_map_lookup.get(asgs_type, common_tag_map)

    ignore_geom = False
    if asgs_type == "STATE" or asgs_type == "AUS":
        ignore_geom = True

    for object_id, feat_elem in features_source:  # type: int, etree._Element
        gj_dict = {"type": "Feature", "id": object_id, "geometry": {},
                   "properties": {}}
        used_tags = set()
        for r in feat_elem.iterchildren():  # type: etree._Element
            try:
                var = tag_map[r.tag]
            except KeyError:
                used_tags.add(r.tag.upper())
                continue
            if isinstance(var, (list, tuple)):
                tokens = var[0:-1]
                var = var[-1]
                if LOCAL_LOOKUP_TOKEN in tokens:
                    # Don't process this tag yet, do it after all of the other WFS tags
                    continue
            used_tags.add(r.tag.upper())
            if var in is_geom and ignore_geom:
                continue
            if var in to_converter:
                conv_func = to_converter[var]
                val = conv_func(r)
            else:
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
        to_lookup = []
        for t in tag_map:
            if t.upper() not in used_tags:
                var = tag_map[t]
                lookup_tuple = None
                if isinstance(var, (list, tuple)):
                    tokens = var[0:-1]
                    var = var[-1]
                    if LOCAL_LOOKUP_TOKEN in tokens:
                        lookup_name = "{}_to_{}".format(asgs_type.lower(), var.lower())
                        lookup_table = LOCAL_DATA_VAL_LOOKUPS.get(lookup_name, None)
                        if lookup_table is None:
                            raise RuntimeError("No local lookup table available for {}".format(lookup_name))
                        # hardcoded "code" here for now, assume always lookup based on code
                        lookup_tuple = (lookup_table, "code", var)
                if lookup_tuple is None:
                    raise RuntimeError("Need but didn't find tag: {}".format(t))
                to_lookup.append(lookup_tuple)
        for l in to_lookup:
            lookup_table, key, var = l
            try:
                key = gj_dict['properties'][key]
            except LookupError:
                raise
            try:
                ikey = int(key)
            except ValueError:
                ikey = None
            val = lookup_table.get(ikey, None) if ikey is not None else None
            if val is None:
                try:
                    val = lookup_table[key]
                except LookupError:
                    raise RuntimeError("Cannot get local lookup value for item with key: {}".format(key))
            gj_dict['properties'][var] = val
        features_list.append(gj_dict)
    return features_list


def asgs_features_triples_converter(asgs_type, canonical_uri, *args, mappings='geosparql'):
    # this coverter is used for the "asgs" and "geosparql" ontology mappings
    if len(args) < 1:
        return None
    wfs_features = args[0]
    if len(wfs_features) < 1:
        return None
    if mappings == 'loci':
        lazy_id = str(canonical_uri).split('/')[-1]
        no_triples = set()
        to_converter = {
            'shape': lambda x: (
            no_triples, URIRef("".join([conf.GEOMETRY_SERVICE_URI, geometry_service_routes[asgs_type], lazy_id]))),
            'shape_area': partial(gml_extract_shapearea_to_geox_area, crs=CRS_EPSG["3857"]), # cartesian area from asgs using "pseudo-mercator" projection
            'albers_area': partial(gml_extract_shapearea_to_geox_area,
                                   extra_transform=lambda x: (set(), float(x) * 1000000.0), crs=CRS_EPSG["3577"]),# cartesian GDA-94 CRS using "Albers_Conic_Equal_Area" projection
            'sa1': lambda x: (no_triples, URIRef(conf.URI_SA1_INSTANCE_BASE + x.text)),
            'sa2': lambda x: (no_triples, URIRef(conf.URI_SA2_INSTANCE_BASE + x.text)),
            'sa3': lambda x: (no_triples, URIRef(conf.URI_SA3_INSTANCE_BASE + x.text)),
            'sa4': lambda x: (no_triples, URIRef(conf.URI_SA4_INSTANCE_BASE + x.text)),
            'dzn': lambda x: (no_triples, URIRef(conf.URI_DZN_INSTANCE_BASE + x.text)),
            'ssc': lambda x: (no_triples, URIRef(conf.URI_SSC_INSTANCE_BASE + x.text)),
            'nrmr': lambda x: (no_triples, URIRef(conf.URI_NRMR_INSTANCE_BASE + x.text)),
            'gccsa': lambda x: (no_triples, URIRef(conf.URI_GCCSA_INSTANCE_BASE + x.text)),
            'iloc': lambda x: (no_triples, URIRef(conf.URI_ILOC_INSTANCE_BASE + x.text)),
            'ucl': lambda x: (no_triples, URIRef(conf.URI_UCL_INSTANCE_BASE + x.text)),
            'sua': lambda x: (no_triples, URIRef(conf.URI_SUA_INSTANCE_BASE + x.text)),
            'ra': lambda x: (no_triples, URIRef(conf.URI_RA_INSTANCE_BASE + x.text)),
            'state': lambda x: (no_triples, URIRef(conf.URI_STATE_INSTANCE_BASE + state_id_map.get(int(x.text), 'OT'))),
            'code': lambda x: (no_triples, Literal(x.text, datatype=feature_identification_types[asgs_type])),
            'category_code': lambda x: (no_triples, ASGS_CAT.term(x.text))
        }
        to_int = ('object_id',)
    else:
        to_converter = {
            'shape': gml_extract_geom_to_geosparql,
            'shape_area': partial(gml_extract_shapearea_to_geox_area, crs=CRS_EPSG["3857"]), #cartesian area from asgs using "pseudo-mercator" projection
            'albers_area': partial(gml_extract_shapearea_to_geox_area, extra_transform=lambda x: (set(), float(x)*1000000), crs=CRS_EPSG["3577"]) #cartesian GDA-94 CRS using "Albers_Conic_Equal_Area" projection
        }
        to_int = ('object_id', 'category', 'state')
    to_float = ('shape_length',)
    is_geom = ('shape',)

    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    tag_map = tag_map_lookup.get(asgs_type, common_tag_map)
    predicate_map = predicate_map_lookup[mappings].get(asgs_type, common_predicate_map_asgs)
    ignore_geom = False
    if mappings == "loci" or asgs_type == "STATE" or asgs_type == "AUS":
        ignore_geom = True

    triples = set()
    feature_nodes = []
    for object_id, feat_elem in features_source:  # type: int, etree._Element
        feature_uri = rdflib.URIRef(canonical_uri)
        triples.add((feature_uri, RDF_a, GEO_Feature))
        triples.add((feature_uri, RDF_a, ASGS.Feature))
        used_tags = set()
        kv_map = {}
        for c in feat_elem.iterchildren():  # type: etree._Element
            try:
                var = tag_map[c.tag]
            except KeyError:
                used_tags.add(c.tag.upper())
                continue
            if isinstance(var, (list, tuple)):
                tokens = var[0:-1]
                var = var[-1]
                if LOCAL_LOOKUP_TOKEN in tokens:
                    continue
            used_tags.add(c.tag.upper())
            if var in is_geom and ignore_geom:
                continue
            if var in to_converter:
                conv_func = to_converter[var]
                _triples, val = conv_func(c)
                for (s, p, o) in iter(_triples):
                    triples.add((s, p, o))
            else:
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
                if predicate is INVERSE_TOKEN or predicate is IGNORE_TOKEN:
                    continue
                if not isinstance(predicate, list):
                    predicate = [predicate]
                for p in predicate:
                    if p is INVERSE_TOKEN:
                        continue
                    triples.add((feature_uri, p, val))
                    kv_map[var] = val
            else:
                if mappings == "loci":
                    if var == "object_id":
                        pass  # we don't care about the internal ASGS object id
                    elif var == "shape_length":
                        pass  # we can't represent feature length in LOCI RDF yet
                    else:
                        raise NotImplementedError(var)
                elif RDF_INCLUDE_UNKNOWN_PREDICATES:
                        dummy_prop = URIRef("{}/{}".format("WFS", var))
                        triples.add((feature_uri, dummy_prop, val))
                else:
                    pass

        to_lookup = []
        for t in tag_map:
            if t.upper() not in used_tags:
                var = tag_map[t]
                lookup_tuple = None
                if isinstance(var, (list, tuple)):
                    tokens = var[0:-1]
                    var = var[-1]
                    if LOCAL_LOOKUP_TOKEN in tokens:
                        lookup_name = "{}_to_{}".format(asgs_type.lower(), var.lower())
                        lookup_table = LOCAL_DATA_VAL_LOOKUPS.get(lookup_name, None)
                        if lookup_table is None:
                            raise RuntimeError("No local lookup table available for {}".format(lookup_name))
                        if var in predicate_map:
                            found_predicates = []
                            predicate = predicate_map[var]
                            if predicate is INVERSE_TOKEN:
                                continue
                            if not isinstance(predicate, list):
                                predicate = [predicate]
                            for p in predicate:
                                if p is INVERSE_TOKEN:
                                    continue
                                found_predicates.append(p)
                        else:
                            found_predicates = [URIRef(var)]
                        # hardcoded "code" here for now, assume always lookup based on code
                        lookup_tuple = (lookup_table, "code", var, found_predicates)
                if lookup_tuple is None:
                    raise RuntimeError("Need but didn't find tag: {}".format(t))
                to_lookup.append(lookup_tuple)
        for l in to_lookup:
            lookup_table, key, var, preds = l
            try:
                key = kv_map[key]
            except LookupError:
                raise
            try:
                ikey = int(key)
            except ValueError:
                ikey = None
            val = lookup_table.get(ikey, None) if ikey is not None else None
            if val is None:
                try:
                    val = lookup_table[key]
                except LookupError:
                    raise RuntimeError("Cannot get local lookup value for item with key: {}".format(key))
            if var in to_converter:
                conv_func = to_converter[var]
                try:
                    c = FakeXMLElement(var, str(val))
                    _triples, val = conv_func(c)
                except Exception as e:
                    raise
                for (s, p, o) in iter(_triples):
                    triples.add((s, p, o))
            for p in preds:
                triples.add((feature_uri, p, val))

        features_list.append(feature_uri)
    return triples, feature_nodes


# def asgs_features_loci_converter(asgs_type, canonical_uri,  wfs_features):
#     # this converter is used for the "loci" ontology mappings
#     if len(wfs_features) < 1:
#         return None
#
#     to_float = ('shape_length',)
#     is_geom = ('shape',)
#
#     features_list = []
#     if isinstance(wfs_features, (dict,)):
#         features_source = wfs_features.items()
#     elif isinstance(wfs_features, (list, set)):
#         features_source = iter(wfs_features)
#     else:
#         features_source = [wfs_features]
#
#     tag_map = tag_map_lookup.get(asgs_type, common_tag_map)
#     predicate_map = predicate_map_lookup['loci'].get(asgs_type, common_predicate_map_asgs)
#
#     triples = set()
#     feature_nodes = []
#     for object_id, feat_elem in features_source:  # type: int, etree._Element
#         feature_uri = rdflib.URIRef(canonical_uri)
#         triples.add((feature_uri, RDF_a, GEO_Feature))
#         triples.add((feature_uri, RDF_a, ASGS.Feature))
#         used_tags = set()
#         kv_map = {}
#         for c in feat_elem.iterchildren():  # type: etree._Element
#             try:
#                 var = tag_map[c.tag]
#             except KeyError:
#                 used_tags.add(c.tag.upper())
#                 continue
#             if isinstance(var, (list, tuple)):
#                 tokens = var[0:-1]
#                 var = var[-1]
#                 if LOCAL_LOOKUP_TOKEN in tokens:
#                     continue
#             used_tags.add(c.tag.upper())
#             if var in to_converter:
#                 conv_func = to_converter[var]
#                 try:
#                     _triples, val = conv_func(c)
#                 except Exception as e:
#                     print(e)
#                     raise
#                 for (s, p, o) in iter(_triples):
#                     triples.add((s, p, o))
#             else:
#                 val = c.text
#             if var in to_float:
#                 val = Literal(float(val))
#             elif var in to_int:
#                 try:
#                     val = int(val)
#                 except ValueError:
#                     val = str(val)
#                 val = Literal(val)
#             else:
#                 if not isinstance(val, (URIRef, Literal, BNode)):
#                     val = Literal(str(val))
#             if var in is_geom:
#                 triples.add((feature_uri, GEO_hasGeometry, val))
#             elif var in predicate_map.keys():
#                 predicate = predicate_map[var]
#                 if predicate is INVERSE_TOKEN:
#                     continue
#                 if not isinstance(predicate, list):
#                     predicate = [predicate]
#                 for p in predicate:
#                     if p is INVERSE_TOKEN:
#                         continue
#                     triples.add((feature_uri, p, val))
#             else:
#                 if var == "object_id":
#                     pass  # we don't care about the internal ASGS object id
#                 elif var == "shape_length":
#                     pass  # we can't represent feature length in LOCI RDF yet
#                 else:
#                     raise NotImplementedError(var)
#                 #pass  # do nothing with predicates we don't know
#         to_lookup = []
#         for t in tag_map:
#             if t.upper() not in used_tags:
#                 var = tag_map[t]
#                 lookup_tuple = None
#                 if isinstance(var, (list, tuple)):
#                     tokens = var[0:-1]
#                     var = var[-1]
#                     if LOCAL_LOOKUP_TOKEN in tokens:
#                         lookup_name = "{}_to_{}".format(asgs_type.lower(), var.lower())
#                         lookup_table = LOCAL_DATA_VAL_LOOKUPS.get(lookup_name, None)
#                         if lookup_table is None:
#                             raise RuntimeError("No local lookup table available for {}".format(lookup_name))
#                         if var in predicate_map:
#                             found_predicates = []
#                             predicate = predicate_map[var]
#                             if predicate is INVERSE_TOKEN:
#                                 continue
#                             if not isinstance(predicate, list):
#                                 predicate = [predicate]
#                             for p in predicate:
#                                 if p is INVERSE_TOKEN:
#                                     continue
#                                 found_predicates.append(p)
#                         else:
#                             found_predicates = [URIRef(var)]
#                         # hardcoded "code" here for now, assume always lookup based on code
#                         lookup_tuple = (lookup_table, "code", var, found_predicates)
#                 if lookup_tuple is None:
#                     raise RuntimeError("Need but didn't find tag: {}".format(t))
#                 to_lookup.append(lookup_tuple)
#         for l in to_lookup:
#             lookup_table, key, var, preds = l
#             try:
#                 key = kv_map[key]
#             except LookupError:
#                 raise
#             try:
#                 ikey = int(key)
#             except ValueError:
#                 ikey = None
#             val = lookup_table.get(ikey, None) if ikey is not None else None
#             if val is None:
#                 try:
#                     val = lookup_table[key]
#                 except LookupError:
#                     raise RuntimeError("Cannot get local lookup value for item with key: {}".format(key))
#             if var in to_converter:
#                 conv_func = to_converter[var]
#                 try:
#                     c = object()
#                     c.text = str(val)
#                     _triples, val = conv_func(c)
#                 except Exception as e:
#                     raise
#                 for (s, p, o) in iter(_triples):
#                     triples.add((s, p, o))
#             for p in preds:
#                 triples.add((feature_uri, p, val))
#         features_list.append(feature_uri)
#     return triples, feature_nodes

def extract_asgs_features_as_geojson(asgs_type, tree):
    geojson_features = wfs_extract_features_as_geojson(
        tree, 'WFS', asgs_type,
        partial(asgs_features_geojson_converter, asgs_type))
    return geojson_features


def extract_asgs_features_as_rdf(asgs_type, tree, ont_conv, g=None):
    triples, features = wfs_extract_features_with_rdf_converter(
        tree, 'WFS', asgs_type, ont_conv)
    if g is None:
        g = rdflib.Graph()
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
    # uncomment to see the full XML dump
    #s = etree.tostring(tree, pretty_print=True)
    #print(s.decode('utf-8'))
    return tree


class ASGSFeature(ASGSModel):
    # INDEX_URI_TEMPLATE = conf.WFS_SERVICE_BASE_URI + \
    #     '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
    #     '&propertyName={propertyname}' \
    #     '&sortBy={propertyname}&startIndex={startindex}&count={count}'
    INDEX_URI_TEMPLATE = conf.WFS_SERVICE_BASE_URI + '?' + \
        urlencode({
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typeName': '{typename}',
            'propertyName': '{propertyname}',
            'sortBy': '{propertyname}',
            'startIndex': '{startindex}',
            'count': '{count}'
        }, safe="{}")

    # FEATURE_URI_TEMPLATE = conf.WFS_SERVICE_BASE_URI + \
    #     '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
    #     '&Filter=<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>' \
    #     '{propertyname}</ogc:PropertyName><ogc:Literal>{featureid}' \
    #     '</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>'
    FEATURE_URI_TEMPLATE = conf.WFS_SERVICE_BASE_URI + '?' + \
        urlencode({
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typeName': '{typename}',
            'Filter': '<ogc:Filter><ogc:PropertyIsEqualTo>' \
                      '<ogc:PropertyName>{propertyname}</ogc:PropertyName>' \
                      '<ogc:Literal>{featureid}</ogc:Literal>' \
                      '</ogc:PropertyIsEqualTo></ogc:Filter>'
        }, safe="{}")

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
        return "{} Feature #{}".format(asgs_type, instance_id)

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
        elif asgs_type == "GCCSA":
            return url_for("controller.redirect_gccsa", gccsa=instance_id)
        elif asgs_type == "SUA":
            return url_for("controller.redirect_sua", sua=instance_id)
        elif asgs_type == "ILOC":
            return url_for("controller.redirect_iloc", iloc=instance_id)
        elif asgs_type == "IARE":
            return url_for("controller.redirect_iare", iare=instance_id)
        elif asgs_type == "IREG":
            return url_for("controller.redirect_ireg", ireg=instance_id)
        elif asgs_type == "UCL":
            return url_for("controller.redirect_ucl", ucl=instance_id)
        elif asgs_type == "SOSR":
            return url_for("controller.redirect_sosr", sosr=instance_id)
        elif asgs_type == "SOS":
            return url_for("controller.redirect_sos", sos=instance_id)
        elif asgs_type == "RA":
            return url_for("controller.redirect_ra", ra=instance_id)
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
        deets = asgs_feature['properties']
        if 'state' in deets and 'state_abbrev' not in deets:
            deets['state_abbrev'] = state_id_map.get(int(deets['state']), "OT")
        self.properties = deets

    @classmethod
    def determine_asgs_type(cls, instance_uri):
        """
        Determine the ASGS underlying WFS TypeName
        for when we only have a LOCI URI to go on.
        :param instance_uri: The Loci URI to get a type of
        :type instance_uri: str
        :return: the WFS TypeName to use when querying the backend
        :rtype: str
        """
        # Note, this is an awful way of doing it, we need a better
        # mapping of Feature URI ->to-> WFS TypeName
        if '/meshblock/' in instance_uri:
            return 'MB'
        elif '/statesuburb/' in instance_uri:
            return 'SSC'
        elif '/sectionofstate/' in instance_uri:
            return 'SOS'
        elif '/indigenousarea/' in instance_uri:
            return 'IARE'
        elif '/remotenessarea/' in instance_uri:
            return 'RA'
        elif '/indigenousregion/' in instance_uri:
            return 'IREG'
        elif '/stateorterritory/' in instance_uri:
            return 'STATE'
        elif '/destinationzone/' in instance_uri:
            return 'DZN'
        elif '/indigenouslocation/' in instance_uri:
            return 'ILOC'
        elif '/sectionofstaterange/' in instance_uri:
            return 'SOSR'
        elif '/significanturbanarea/' in instance_uri:
            return 'SUA'
        elif '/statisticalarealevel1/' in instance_uri:
            return 'SA1'
        elif '/statisticalarealevel2/' in instance_uri:
            return 'SA2'
        elif '/statisticalarealevel3/' in instance_uri:
            return 'SA3'
        elif '/statisticalarealevel4/' in instance_uri:
            return 'SA4'
        elif '/urbancentreandlocality/' in instance_uri:
            return 'UCL'
        elif '/naturalresourcemanagementregion/' in instance_uri:
            return 'NRMR'
        elif '/greatercapitalcitystatisticalarea/' in instance_uri:
            return 'GCCSA'
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
            self.asgs_type, self.xml_tree,
            partial(asgs_features_triples_converter, self.asgs_type, self.uri, mappings='geosparql'),
            graph)

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
            self.asgs_type, self.xml_tree,
            partial(asgs_features_triples_converter, self.asgs_type, self.uri, mappings='loci'),
            graph)

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
                g = self.as_geosparql()
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
            reg_reg = URIRef('http://purl.org/linked-data/registry#register')
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
                    g.add((feat, reg_reg, URIRef(conf.URI_MESHBLOCK_INSTANCE_BASE)))
            elif self.asgs_type == "SA1":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel1))
                sa2 = URIRef(conf.URI_SA2_INSTANCE_BASE + deets['sa2'])
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SA1_INSTANCE_BASE)))
                    g.add((sa2, GEO_contains, feat))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_SA1_INSTANCE_BASE)))
                    g.add((sa2, ASGS.isStatisticalAreaLevel2Of, feat))
                if 'iloc' in deets:
                    iloc_code = Literal(str(deets['iloc']))
                    iloc = URIRef(conf.URI_ILOC_INSTANCE_BASE+str(deets['iloc']))
                    g.add((iloc, RDF_a, URIRef(conf.URI_ILOC_CLASS)))

                    if is_loci_profile:
                        g.add((iloc, GEO_contains, feat))
                        iloc_code._datatype = ASGS_ID.term('ilocCode2016')
                        g.add((iloc, DCTERMS.identifier, iloc_code))
                    else:
                        g.add((iloc, ASGS.contains, feat))
                        g.add((iloc, ASGS.nrmrCode2016, iloc_code))
                if 'ucl' in deets:
                    ucl_code = Literal(str(deets['ucl']))
                    ucl = URIRef(conf.URI_UCL_INSTANCE_BASE+str(deets['ucl']))
                    g.add((ucl, RDF_a, URIRef(conf.URI_UCL_CLASS)))

                    if is_loci_profile:
                        g.add((ucl, GEO_contains, feat))
                        ucl_code._datatype = ASGS_ID.term('uclCode2016')
                        g.add((ucl, DCTERMS.identifier, ucl_code))
                    else:
                        g.add((ucl, ASGS.contains, feat))
                        g.add((ucl, ASGS.uclCode2016, ucl_code))
                if 'ra' in deets:
                    ra_code = Literal(str(deets['ra']))
                    ra = URIRef(conf.URI_RA_INSTANCE_BASE+str(deets['ra']))
                    g.add((ra, RDF_a, URIRef(conf.URI_RA_CLASS)))

                    if is_loci_profile:
                        g.add((ra, GEO_contains, feat))
                        ra_code._datatype = ASGS_ID.term('raCode2016')
                        g.add((ra, DCTERMS.identifier, ra_code))
                    else:
                        g.add((ra, ASGS.contains, feat))
                        g.add((ra, ASGS.raCode2016, ra_code))
            elif self.asgs_type == "SA2":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel2))
                sa3 = URIRef(conf.URI_SA3_INSTANCE_BASE + deets['sa3'])
                g.add((sa3, ASGS.isStatisticalAreaLevel3Of, feat))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SA2_INSTANCE_BASE)))
                    g.add((sa3, GEO_contains, feat))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_SA2_INSTANCE_BASE)))
                    g.add((sa3, ASGS.isStatisticalAreaLevel3Of, feat))
                if 'sua' in deets:
                    sua_code = Literal(str(deets['sua']))
                    sua = URIRef(conf.URI_RA_INSTANCE_BASE+str(deets['sua']))
                    g.add((sua, RDF_a, URIRef(conf.URI_SUA_CLASS)))

                    if is_loci_profile:
                        g.add((sua, GEO_contains, feat))
                        sua_code._datatype = ASGS_ID.term('suaCode2016')
                        g.add((sua, DCTERMS.identifier, sua_code))
                    else:
                        g.add((sua, ASGS.contains, feat))
                        g.add((sua, ASGS.suaCode2016, sua_code))

            elif self.asgs_type == "SA3":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel3))
                sa4 = URIRef(conf.URI_SA4_INSTANCE_BASE + deets['sa4'])
                g.add((sa4, ASGS.isStatisticalAreaLevel4Of, feat))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SA3_INSTANCE_BASE)))
                    g.add((sa4, GEO_contains, feat))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_SA3_INSTANCE_BASE)))
                    g.add((sa4, ASGS.isStatisticalAreaLevel4Of, feat))
            elif self.asgs_type == "SA4":
                g.add((feat, RDF_a, ASGS.StatisticalAreaLevel4))
                if 'gccsa' in deets:
                    gccsa_code = Literal(str(deets['gccsa']))
                    gccsa = URIRef(conf.URI_GCCSA_INSTANCE_BASE+str(deets['gccsa']))
                    g.add((gccsa, RDF_a, URIRef(conf.URI_GCCSA_CLASS)))
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
                    g.add((feat, reg_reg, URIRef(conf.URI_SA4_INSTANCE_BASE)))
            elif self.asgs_type == "STATE":
                g.add((feat, RDF_a, ASGS.StateOrTerritory))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_STATE_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_STATE_INSTANCE_BASE)))
            elif self.asgs_type == "GCCSA":
                g.add((feat, RDF_a, ASGS.GreaterCapitalCityStatisticalArea))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_GCCSA_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_GCCSA_INSTANCE_BASE)))
            elif self.asgs_type == "SUA":
                g.add((feat, RDF_a, ASGS.SignificantUrbanArea))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SUA_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_SUA_INSTANCE_BASE)))
            elif self.asgs_type == "RA":
                g.add((feat, RDF_a, ASGS.RemotenessArea))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_RA_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_RA_INSTANCE_BASE)))
            elif self.asgs_type == "ILOC":
                g.add((feat, RDF_a, ASGS.IndigenousLocation))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_ILOC_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_ILOC_INSTANCE_BASE)))
            elif self.asgs_type == "IARE":
                g.add((feat, RDF_a, ASGS.IndigenousArea))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_IARE_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_IARE_INSTANCE_BASE)))
            elif self.asgs_type == "IREG":
                g.add((feat, RDF_a, ASGS.IndigenousRegion))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_IREG_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_IREG_INSTANCE_BASE)))
            elif self.asgs_type == "UCL":
                g.add((feat, RDF_a, ASGS.UrbanCentreAndLocality))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_UCL_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_UCL_INSTANCE_BASE)))
            elif self.asgs_type == "SOSR":
                g.add((feat, RDF_a, ASGS.SectionOfStateRange))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SOSR_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_SOSR_INSTANCE_BASE)))
            elif self.asgs_type == "SOS":
                g.add((feat, RDF_a, ASGS.SectionOfState))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_SOS_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_SOS_INSTANCE_BASE)))
            else:
                g.add((feat, RDF_a, ASGS.Australia))
                # register
                if is_loci_profile:
                    g.add((feat, LOCI.isMemberOf, URIRef(conf.URI_AUS_INSTANCE_BASE)))
                else:
                    g.add((feat, reg_reg, URIRef(conf.URI_AUS_INSTANCE_BASE)))
            if self.asgs_type != "AUS" and self.asgs_type != "STATE":
                if 'state' in deets:
                    state_uri = URIRef(conf.URI_STATE_INSTANCE_BASE + state_id_map.get(int(deets['state']), 'OT'))
                    if is_loci_profile:
                        g.add((feat, GEO_within, state_uri))
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
    def total_gccsas():
        return GCCSA_COUNT

    @staticmethod
    def total_suas():
        return SUA_COUNT

    @staticmethod
    def total_ilocs():
        return ILOC_COUNT

    @staticmethod
    def total_iareas():
        return IARE_COUNT

    @staticmethod
    def total_iregs():
        return IREG_COUNT

    @staticmethod
    def total_ucls():
        return UCL_COUNT

    @staticmethod
    def total_sosrs():
        return SOSR_COUNT

    @staticmethod
    def total_soss():
        return SOS_COUNT

    @staticmethod
    def total_ras():
        return RA_COUNT

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
            tree = etree.parse(resp)  # type: lxml._ElementTree
        wfs_type = ASGS_WFS_LOOKUP[asgs_type]  # type: AsgsWfsType
        items = tree.xpath('//{}/text()'.format(wfs_type.propertyname), namespaces=tree.getroot().nsmap)
        return items

    @classmethod
    def construct_wfs_query_for_index(cls, asgs_type, startindex, count):
        wfs_type = ASGS_WFS_LOOKUP[asgs_type]  # type: AsgsWfsType
        return wfs_type.populate_string(cls.INDEX_URI_TEMPLATE,
                                        startindex=startindex, count=count)

    def get_wfs_query_for_feature_type(self):
        asgs_type = self.asgs_type
        identifier = self.id
        return self.construct_wfs_query_for_feature_type(asgs_type, identifier)

    @classmethod
    def construct_wfs_query_for_feature_type(cls, asgs_type, identifier):
        wfs_type = ASGS_WFS_LOOKUP[asgs_type]  # type: AsgsWfsType
        return wfs_type.populate_string(cls.FEATURE_URI_TEMPLATE,
                                        featureid=identifier)


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
