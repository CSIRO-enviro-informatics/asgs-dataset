# -*- coding: utf-8 -*-
from flask import Blueprint, request, redirect, url_for, Response, render_template
from pyldapi import RegisterOfRegistersRenderer
from flask_cors import CORS
from asgs_dataset.model.asgs_feature import ASGSFeature
from asgs_dataset.view.ldapi import ASGSRegisterRenderer
from asgs_dataset.view.ldapi.asgs_feature import ASGSFeatureRenderer
import asgs_dataset._config as conf
import asgs_dataset.controller.LOCIDatasetRenderer


ctrl = Blueprint('controller', __name__)
CORS(ctrl, automatic_options=True)

#
#   pages
#
@ctrl.route('/', strict_slashes=True)
def home():
    return asgs_dataset.controller.LOCIDatasetRenderer.LOCIDatasetRenderer(request, url=conf.URI_BASE).render()


@ctrl.route('/index.ttl')
def home_ttl():
    return asgs_dataset.controller.LOCIDatasetRenderer.LOCIDatasetRenderer(request, view='dcat', format='text/turtle').render()


@ctrl.route('/other')
def other_abs():
    return render_template("page_other_abs.html")

@ctrl.route('/nonabs')
def non_abs():
    return render_template("page_non_abs.html")
#
#   registers
#
@ctrl.route('/reg/')
def reg():
    return RegisterOfRegistersRenderer(
        request,
        conf.DATA_URI_PREFIX,
        'Register of Registers',
        'The master register of this API',
        conf.APP_DIR + '/rofr.ttl'
    ).render()


@ctrl.route('/stateorterritory/')
def states():
    total = ASGSFeature.total_states()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    # get page of MB URIs from ABS Web Service
    register_states = [str(i) for i in range(1,10)]

    register_renderer = ASGSRegisterRenderer(
        request,
        conf.URI_STATE_INSTANCE_BASE,
        'Register of States or Territories',
        'Australian States and Territories',
        [conf.URI_STATE_CLASS],
        total,
        None,
        super_register=conf.DATA_URI_PREFIX,
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


@ctrl.route('/australia/')
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
        super_register=conf.DATA_URI_PREFIX,
    )
    register_renderer.register_items = register_aus
    return register_renderer.render()


@ctrl.route('/meshblock/')
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
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()


@ctrl.route('/statisticalarealevel1/')
def sa1s():
    total = ASGSFeature.total_sa1s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA1_INSTANCE_BASE,
        'Register of ASGS Statistical Area Level 1 regions',
        'All the ASGS Statistical Area Level 1 regions',
        [conf.URI_SA1_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()


@ctrl.route('/statisticalarealevel2/')
def sa2s():
    total = ASGSFeature.total_sa2s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA2_INSTANCE_BASE,
        'Register of ASGS Statistical Area Level 2 regions',
        'All the ASGS Statistical Area Level 2 regions',
        [conf.URI_SA2_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()


@ctrl.route('/statisticalarealevel3/')
def sa3s():
    total = ASGSFeature.total_sa3s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA3_INSTANCE_BASE,
        'Register of ASGS Statistical Area Level 3 regions',
        'All the ASGS Statistical Area Level 3 regions',
        [conf.URI_SA3_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()


@ctrl.route('/statisticalarealevel4/')
def sa4s():
    total = ASGSFeature.total_sa4s()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SA4_INSTANCE_BASE,
        'Register of ASGS Statistical Area Level 4 regions',
        'All the ASGS Statistical Area Level 4 regions',
        [conf.URI_SA4_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/greatercapitalcitystatisticalarea/')
def gccsas():
    total = ASGSFeature.total_gccsas()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_GCCSA_INSTANCE_BASE,
        'Register of ASGS Greater Capital City Statistical Areas',
        'All the ASGS Greater Capital City Statistical areas',
        [conf.URI_GCCSA_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/significanturbanarea/')
def suas():
    total = ASGSFeature.total_suas()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SUA_INSTANCE_BASE,
        'Register of ASGS Significant Urban Areas',
        'All the ASGS Significant Urban Areas',
        [conf.URI_SUA_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/remotenessarea/')
def ras():
    total = ASGSFeature.total_ras()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_RA_INSTANCE_BASE,
        'Register of ASGS Remoteness Areas',
        'All the ASGS Remoteness Areas',
        [conf.URI_RA_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/urbancentreandlocality/')
def ucls():
    total = ASGSFeature.total_ucls()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_UCL_INSTANCE_BASE,
        'Register of ASGS Urban Centres and Localities',
        'All the ASGS Urban Centres and Localities',
        [conf.URI_UCL_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/sectionofstaterange/')
def sosrs():
    total = ASGSFeature.total_sosrs()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SOSR_INSTANCE_BASE,
        'Register of ASGS Section of State Ranges',
        'All the ASGS Section of State Ranges',
        [conf.URI_SOSR_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/sectionofstate/')
def soss():
    total = ASGSFeature.total_soss()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_SOS_INSTANCE_BASE,
        'Register of ASGS Sections of States',
        'All the ASGS Sections of States',
        [conf.URI_SOS_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/indigenouslocation/')
def ilocs():
    total = ASGSFeature.total_ilocs()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_ILOC_INSTANCE_BASE,
        'Register of ASGS Indigenous Locations',
        'All the ASGS Indigenous Locations',
        [conf.URI_ILOC_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/indigenousarea/')
def iareas():
    total = ASGSFeature.total_iareas()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_IARE_INSTANCE_BASE,
        'Register of ASGS Indigenous Areas',
        'All the ASGS Indigenous Areas',
        [conf.URI_IARE_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()

@ctrl.route('/indigenousregion/')
def iregs():
    total = ASGSFeature.total_iregs()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        conf.URI_IREG_INSTANCE_BASE,
        'Register of ASGS Indigenous Regions',
        'All the ASGS Indigenous Regions',
        [conf.URI_IREG_CLASS],
        total,
        ASGSFeature,
        super_register=conf.DATA_URI_PREFIX,
    ).render()
#
#   instances
#
@ctrl.route('/object')
def object():
    if request.args.get('uri') is not None and str(request.args.get('uri')).startswith('http'):
        uri = request.args.get('uri')
    else:
        return Response('You must supply the URI if a resource with ?uri=...', status=400, mimetype='text/plain')

    # protecting against '+' being rendered as a space in MTs like application/rdf+xml
    uri = uri.replace(' ', '+')

    return ASGSFeatureRenderer(request, uri, None).render()


# mediatype alias
@ctrl.route('/meshblock/<path:mb>')
def redirect_meshblock(mb):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_MESHBLOCK_INSTANCE_BASE + mb, **args))


# state alias
@ctrl.route('/stateorterritory/<path:state>')
def redirect_state(state):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_STATE_INSTANCE_BASE + state, **args))


# aus alias
@ctrl.route('/australia/<string:code>')
def redirect_aus(code):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_AUS_INSTANCE_BASE + code, **args))


# sa1 alias
@ctrl.route('/statisticalarealevel1/<path:sa1>')
def redirect_sa1(sa1):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA1_INSTANCE_BASE + sa1, **args))


# sa2 alias
@ctrl.route('/statisticalarealevel2/<path:sa2>')
def redirect_sa2(sa2):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA2_INSTANCE_BASE + sa2, **args))


# sa3 alias
@ctrl.route('/statisticalarealevel3/<path:sa3>')
def redirect_sa3(sa3):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA3_INSTANCE_BASE + sa3, **args))


# sa4 alias
@ctrl.route('/statisticalarealevel4/<path:sa4>')
def redirect_sa4(sa4):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SA4_INSTANCE_BASE + sa4, **args))

@ctrl.route('/greatercapitalcitystatisticalarea/<path:gccsa>')
def redirect_gccsa(gccsa):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_GCCSA_INSTANCE_BASE + gccsa, **args))

@ctrl.route('/significanturbanarea/<path:sua>')
def redirect_sua(sua):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SUA_INSTANCE_BASE + sua, **args))

@ctrl.route('/remotenessarea/<path:ra>')
def redirect_ra(ra):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_RA_INSTANCE_BASE + ra, **args))

@ctrl.route('/urbancentreandlocality/<path:ucl>')
def redirect_ucl(ucl):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_UCL_INSTANCE_BASE + ucl, **args))

@ctrl.route('/sectionofstaterange/<path:sosr>')
def redirect_sosr(sosr):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SOSR_INSTANCE_BASE + sosr, **args))

@ctrl.route('/sectionofstate/<path:sos>')
def redirect_sos(sos):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_SOS_INSTANCE_BASE + sos, **args))

@ctrl.route('/indigenouslocation/<path:iloc>')
def redirect_iloc(iloc):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_ILOC_INSTANCE_BASE + iloc, **args))

@ctrl.route('/indigenousarea/<path:iare>')
def redirect_iare(iare):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_IARE_INSTANCE_BASE + iare, **args))

@ctrl.route('/indigenousregion/<path:ireg>')
def redirect_ireg(ireg):
    args = request.args
    return redirect(url_for('controller.object', uri=conf.URI_IREG_INSTANCE_BASE + ireg, **args))
