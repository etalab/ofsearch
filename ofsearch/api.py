from flask import current_app
from flask_restplus import Api, Resource, cors, fields

api = Api(
    title='OFSearch API',
    version='1.0',
    description='Search and consult french training organizations',
    decorators=[cors.crossdomain(origin='*', credentials=True)],
)


parser = api.parser()
parser.add_argument('q', type=str, help='The search query', required=True)
parser.add_argument('page', type=int, help='Page to display', default=1)
parser.add_argument('limit', type=int, help='Max number of results per page', default=20)

specialty = api.model('Specialty', {
    'code': fields.Integer,
    'trainees': fields.Integer,
    'hours': fields.Integer,
})

organization = api.model('Organization', {
    'numero_de_da': fields.String,
    'form_total': fields.Integer,
    'da_siren': fields.String,
    'da_no_etab': fields.String,
    'da_raison_sociale': fields.String,
    'adr_rue_physique': fields.String,
    'adr_rue_complement_physique': fields.String,
    'adr_code_postal_physique': fields.String,
    'adr_ville_physique': fields.String,
    'adr_rue_postale': fields.String,
    'adr_rue_complement_postale': fields.String,
    'adr_code_postal_postale': fields.String,
    'adr_ville_postale': fields.String,
    'specialties': fields.List(fields.Nested(specialty))
})

search_results = api.model('SearchResult', {
    'query': fields.String,
    'page': fields.Integer,
    'limit': fields.Integer,
    'total': fields.Integer,
    'results': fields.List(fields.Nested(organization)),
})


class WithDb(object):
    @property
    def db(self):
        return current_app.extensions['db']


@api.route('/organizations/')
@api.expect(parser)
class Search(WithDb, Resource):
    @api.doc('search')
    @api.marshal_with(search_results)
    def get(self):
        '''Search organizations on their name, SIREN or declaration number'''
        args = parser.parse_args()
        return self.db.search(args['q'], page=args['page'], limit=args['limit'])


@api.route('/organizations/<id>')
@api.param('id', 'A declaration number or a SIREN')
class Display(WithDb, Resource):
    @api.doc('display')
    @api.response(404, 'No organization found matching this SIREN or this declaration number')
    @api.marshal_with(organization)
    def get(self, id):
        '''Get an organization given its SIREN or its declaration number'''
        doc = self.db.get(id)
        if not doc:
            api.abort(404, 'No organization found matching this identifier')


@api.route('/specialties/')
class Specialties(WithDb, Resource):
    @api.doc('specialties')
    def get(self):
        '''Map specialties code to their label'''
        return self.db.specialties
