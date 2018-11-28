from flask import Blueprint, request, redirect, url_for, Response, render_template
from pyldapi import RegisterOfRegistersRenderer

from asgs_dataset.model.asgs_feature import ASGSFeature
from asgs_dataset.view.ldapi import ASGSRegisterRenderer
from asgs_dataset.view.ldapi.asgs_feature import ASGSFeatureRenderer
import asgs_dataset._config as conf
from asgs_dataset.model.meshblock import MeshBlock
import asgs_dataset.controller.LOCIDatasetRenderer


routes = Blueprint('controller', __name__)


#
#   pages
#
@routes.route('/', strict_slashes=True)
def home():
    return asgs_dataset.controller.LOCIDatasetRenderer.LOCIDatasetRenderer(request, url=conf.URI_BASE).render()


@routes.route('/index.ttl')
def home_ttl():
    return asgs_dataset.controller.LOCIDatasetRenderer.LOCIDatasetRenderer(request, view='dcat', format='text/turtle').render()


#
#   registers
#
@routes.route('/reg/')
def reg():
    return RegisterOfRegistersRenderer(
        request,
        conf.DATA_URI_PREFIX+"/reg",
        'Register of Registers',
        'The master register of this API',
        conf.APP_DIR + '/rofr.ttl'
    ).render()


@routes.route('/state/')
def states():
    total = ASGSFeature.total_states()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    # get page of MB URIs from ABS Web Service
    register_states = [
        'ACT',
        'NT',
        'NSW',
        'NT',
        'OT',
        'SA',
        'TAS',
        'VIC',
        'WA'
    ]

    register_renderer = ASGSRegisterRenderer(
        request,
        conf.URI_STATE_INSTANCE_BASE,
        'Register of States',
        'Australian States and Territories',
        [conf.URI_STATE_CLASS],
        total,
        None,
        super_register=conf.DATA_URI_PREFIX+"/reg",
    )
    # TODO: Determine whether to generate these with canonical_url or local_url!
    # register_renderer.register_items =\
    #     [ (url_for('controller.redirect_state', state=s), s)
    #       for s in register_states ]
    register_renderer.register_items =\
        [
            (conf.URI_STATE_INSTANCE_BASE+s,
             "ASGS Feature State: {}".format(s), s)
            for s in register_states
        ]
    return register_renderer.render()


@routes.route('/australia/')
def aus_index():
    total_australias = 1
    # TODO: Determine whether to generate these with canonical_url or local_url!
    # register_aus = [
    #     (url_for('controller.redirect_aus', code="036"), "Australia (036)")
    # ]
    register_aus = [
        (conf.URI_AUS_INSTANCE_BASE+"036", "Australia (036)", "036")
    ]

    register_renderer = ASGSRegisterRenderer(
        request,
        conf.URI_AUS_INSTANCE_BASE,
        'Register of Australias',
        'How many instances of Australia are there in the Australia index?',
        [conf.URI_AUS_CLASS],
        total_australias,
        None,
        super_register=conf.DATA_URI_PREFIX+"/reg",
    )
    register_renderer.register_items = register_aus
    return register_renderer.render()


@routes.route('/meshblock/')
def meshblocks():
    total = ASGSFeature.total_meshblocks()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_MESHBLOCK_INSTANCE_BASE,
        'Register of ASGS Meshblocks',
        'All the ASGS Meshblocks',
        [conf.URI_MESHBLOCK_CLASS],
        total,
        MeshBlock,
        super_register=conf.DATA_URI_PREFIX+"/reg",
    ).render()


@routes.route('/sa1/')
def sa1s():
    total = ASGSFeature.total_sa1s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA1_INSTANCE_BASE,
        'Register of ASGS SA1 regions',
        'All the ASGS SA1 regions',
        [conf.URI_SA1_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX+"/reg",
    ).render()


@routes.route('/sa2/')
def sa2s():
    total = ASGSFeature.total_sa2s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA2_INSTANCE_BASE,
        'Register of ASGS SA2 regions',
        'All the ASGS SA2 regions',
        [conf.URI_SA2_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX+"/reg",
    ).render()


@routes.route('/sa3/')
def sa3s():
    total = ASGSFeature.total_sa3s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA3_INSTANCE_BASE,
        'Register of ASGS SA3 regions',
        'All the ASGS SA3 regions',
        [conf.URI_SA3_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX+"/reg",
    ).render()


@routes.route('/sa4/')
def sa4s():
    total = ASGSFeature.total_sa4s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA4_INSTANCE_BASE,
        'Register of ASGS SA4 regions',
        'All the ASGS SA4 regions',
        [conf.URI_SA4_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX+"/reg",
    ).render()


#
#   instances
#
@routes.route('/object')
def object():
    if request.args.get('uri') is not None and str(request.args.get('uri')).startswith('http'):
        uri = request.args.get('uri')
    else:
        return Response('You must supply the URI if a resource with ?uri=...', status=400, mimetype='text/plain')

    # protecting against '+' being rendered as a space in MTs like application/rdf+xml
    uri = uri.replace(' ', '+')

    return ASGSFeatureRenderer(request, uri, None).render()


# mediatype alias
@routes.route('/meshblock/<path:mb>')
def redirect_meshblock(mb):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_MESHBLOCK_INSTANCE_BASE + mb, **args))


# state alias
@routes.route('/state/<path:state>')
def redirect_state(state):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_STATE_INSTANCE_BASE + state, **args))


# aus alias
@routes.route('/australia/<string:code>')
def redirect_aus(code):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_AUS_INSTANCE_BASE + code, **args))


# sa1 alias
@routes.route('/sa1/<path:sa1>')
def redirect_sa1(sa1):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA1_INSTANCE_BASE + sa1, **args))


# sa2 alias
@routes.route('/sa2/<path:sa2>')
def redirect_sa2(sa2):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA2_INSTANCE_BASE + sa2, **args))


# sa3 alias
@routes.route('/sa3/<path:sa3>')
def redirect_sa3(sa3):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA3_INSTANCE_BASE + sa3, **args))


# sa4 alias
@routes.route('/sa4/<path:sa4>')
def redirect_sa4(sa4):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA4_INSTANCE_BASE + sa4, **args))
