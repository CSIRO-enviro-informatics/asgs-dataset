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
URI_ASGSFEATURE_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'feature/'])
URI_MESHBLOCK_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'meshblock/'])
URI_AUS_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'australia/'])
URI_STATE_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'stateorterritory/'])
URI_SA1_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel1/'])
URI_SA2_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel2/'])
URI_SA3_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel3/'])
URI_SA4_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'statisticalarealevel4/'])

WFS_SERVICE_BASE_URI = 'https://geo.abs.gov.au/arcgis/services/ASGS2016/{service}/MapServer/WFSServer'