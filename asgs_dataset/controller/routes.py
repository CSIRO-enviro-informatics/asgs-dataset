from flask import Blueprint, request, redirect, url_for, Response, render_template
from pyldapi import RegisterOfRegistersRenderer

from asgs_dataset.model.asgs_feature import ASGSFeature
from asgs_dataset.model.ldapi import ASGSRegisterRenderer
from asgs_dataset.model.ldapi.asgs_feature import ASGSFeatureRenderer
import asgs_dataset._config as conf
from asgs_dataset.model.meshblock import MeshBlock

routes = Blueprint('controller', __name__)

#
#   pages
#
@routes.route('/')
def home():
    return render_template('page_home.html')


#
#   registers
#
@routes.route('/reg/')
def reg():
    return RegisterOfRegistersRenderer(
        request,
        'http://localhost:5000/',
        'Register of Registers',
        'The master register of this API',
        conf.APP_DIR + '/rofr.ttl'
    ).render()


@routes.route('/state/')
def states():
    per_page = request.args.get('per_page', type=int, default=20)
    page = request.args.get('page', type=int, default=1)

    total = ASGSFeature.total_states()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    # get page of MB URIs from ABS Web Service
    q = '''Fake Query {} {}'''.format(per_page, (page - 1) * per_page)
    register = [
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
        'http://localhost:5000/state/',
        'Register of States',
        'Australian States and Territories',
        ['http://test.linked.data.gov.au/def/asgs#State'],
        total,
        None,
        super_register='http://localhost:5000/reg/'
    )
    register_renderer.register_items = register
    return register_renderer.render()


@routes.route('/meshblock/')
def meshblocks():
    per_page = request.args.get('per_page', type=int, default=20)
    page = request.args.get('page', type=int, default=1)

    total = ASGSFeature.total_meshblocks()
    if total is None:
        return Response('ASGS Web Service is unreachable', status=500, mimetype='text/plain')

    return ASGSRegisterRenderer(
        request,
        'http://localhost:5000/policy/',
        'Register of Media Types',
        'All the Media Types in IANA\'s list at https://www.iana.org/assignments/media-types/media-types.xml.',
        ['http://test.linked.data.gov.au/def/asgs#MeshBlock'],
        total,
        MeshBlock
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
    return redirect(url_for('controller.object', uri='http://test.linked.data.gov.au/dataset/asgs/meshblock/' + mb))


# state alias
@routes.route('/state/<path:state>')
def redirect_state(state):
    return redirect(url_for('controller.object', uri='http://test.linked.data.gov.au/dataset/asgs/state/' + state))
