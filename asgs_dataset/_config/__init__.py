from os.path import dirname, realpath, join, abspath

APP_DIR = dirname(dirname(realpath(__file__)))
TEMPLATES_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'templates')
STATIC_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'static')
LOGFILE = APP_DIR + '/flask.log'
DEBUG = True

URI_BASE = "http://linked.data.gov.au"  # must _not_ end in a trailing slash
DEF_URI_PREFIX = '/'.join([URI_BASE, 'def/asgs'])
DATA_URI_PREFIX = '/'.join([URI_BASE, 'dataset/asgs2016'])
#MESHBLOCK_COUNT = 358122
#SA1_COUNT = 57523
#SA2_COUNT = 2310
#SA3_COUNT = 358
#SA4_COUNT = 107
MESHBLOCK_COUNT = 358009
SA1_COUNT = 57490
SA2_COUNT = 2292
SA3_COUNT = 340
SA4_COUNT = 89

URI_ASGSFEATURE_CLASS = "".join([DEF_URI_PREFIX, "#Feature"])
URI_MESHBLOCK_CLASS = "".join([DEF_URI_PREFIX, "#MeshBlock"])
URI_AUS_CLASS = "".join([DEF_URI_PREFIX, "#Australia"])
URI_STATE_CLASS = "".join([DEF_URI_PREFIX, "#StateOrTerritory"])
URI_SA1_CLASS = "".join([DEF_URI_PREFIX, "#StatisticalAreaLevel1"])
URI_SA2_CLASS = "".join([DEF_URI_PREFIX, "#StatisticalAreaLevel2"])
URI_SA3_CLASS = "".join([DEF_URI_PREFIX, "#StatisticalAreaLevel3"])
URI_SA4_CLASS = "".join([DEF_URI_PREFIX, "#StatisticalAreaLevel4"])
URI_DZN_CLASS = "".join([DEF_URI_PREFIX, "#DestinationZone"])
URI_SSC_CLASS = "".join([DEF_URI_PREFIX, "#StateSuburb"])
URI_NRMR_CLASS = "".join([DEF_URI_PREFIX, "#NaturalResourceManagementRegion"])
URI_GCCSA_CLASS = "".join([DEF_URI_PREFIX, "#GreaterCapitalCityStatisticalArea"])
URI_SUA_CLASS = "".join([DEF_URI_PREFIX, "#SignificantUrbanArea"])
URI_RA_CLASS = "".join([DEF_URI_PREFIX, "#RemotenessArea"])
URI_UCL_CLASS = "".join([DEF_URI_PREFIX, "#UrbanCentreAndLocality"])
URI_SOSR_CLASS = "".join([DEF_URI_PREFIX, "#SectionOfStateRange"])
URI_SOS_CLASS = "".join([DEF_URI_PREFIX, "#SectionOfState"])
URI_ILOC_CLASS = "".join([DEF_URI_PREFIX, "#IndigenousLocation"])
URI_IARE_CLASS = "".join([DEF_URI_PREFIX, "#IndigenousArea"])
URI_IREG_CLASS = "".join([DEF_URI_PREFIX, "#IndigenousRegion"])
URI_ASGSFEATURE_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'feature/'])
URI_MESHBLOCK_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'meshblock/'])
URI_AUS_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'australia/'])
URI_STATE_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'stateorterritory/'])
URI_SA1_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel1/'])
URI_SA2_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel2/'])
URI_SA3_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel3/'])
URI_SA4_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel4/'])
URI_DZN_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'destinationzone/'])
URI_SSC_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statesuburb/'])
URI_NRMR_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'naturalresourcemanagementregion/'])
URI_GCCSA_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'greatercapitalcitystatisticalarea/'])
URI_SUA_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'significanturbanarea/'])
URI_RA_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'remotenessarea/'])
URI_UCL_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'urbancentreandlocality/'])
URI_SOSR_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'sectionofstaterange/'])
URI_SOS_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'sectionofstate/'])
URI_ILOC_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'indigenouslocation/'])
URI_IARE_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'indigenousarea/'])
URI_IREG_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'indigenousregion/'])

WFS_SERVICE_BASE_URI = 'https://geo.abs.gov.au/arcgis/services/ASGS2016/{service}/MapServer/WFSServer'
GEOMETRY_SERVICE_HOST = "http://gds.loci.cat"
GEOMETRY_SERVICE_URI = '/'.join([GEOMETRY_SERVICE_HOST, "geometry/"])
#geometry/asgs16_ste/
#geometry/asgs16_sa4/ .. geometry/asgs16_sa1/
#geometry/asgs16_mb/