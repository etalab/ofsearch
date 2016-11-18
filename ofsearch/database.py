import logging
import multiprocessing
import os

from contextlib import contextmanager

from whoosh import fields, index
from whoosh.analysis import NgramWordAnalyzer
from whoosh.qparser import MultifieldParser

log = logging.getLogger(__name__)


DEFAULT_INDEX = 'index'
DEFAULT_MAX_MEMORY = '1024'


def parse_boolean(value):
    '''a failsafe boolean parser'''
    # TODO: need implementation
    return value


def parse_int(value):
    '''a failsafe integer parser'''
    if not value:
        return None
    elif isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception as e:
        log.exception('Unable to parse integer "%s": %s', value, e)
        return None


ngram_analyzer = NgramWordAnalyzer(minsize=3)


class Organization(fields.SchemaClass):
    # numero_de_da : Numéro de la Déclaration d'Activité -
    numero_de_da = fields.ID(stored=True, unique=True)
    # form_total : Nombre de formateurs -
    form_total = fields.NUMERIC(stored=True)
    # da_siren : Numéro de SIREN de la structure -
    da_siren = fields.ID(stored=True, unique=True)
    # da_no_etab : Numéro d'établissement de la structure -
    da_no_etab = fields.ID(stored=True)
    # da_raison_sociale : Raison Sociale -
    da_raison_sociale = fields.TEXT(stored=True, analyzer=ngram_analyzer, phrase=False)
    # sf : Spécialité de Formation -
    # sf = fields.ID
    # nsf : Nombre de stagiaires formés dans la spécialité -
    # nhsf : Nombre d'heures-stagiaires suivies dans la spécialité -
    # adr_rue_physique : Voie de l'adresse physique -
    adr_rue_physique = fields.TEXT(stored=True)
    # adr_rue_complement_physique : Complément de l'adresse physique -
    adr_rue_complement_physique = fields.TEXT(stored=True)
    # adr_code_postal_physique : Code postal de l'adresse physique -
    adr_code_postal_physique = fields.ID(stored=True)
    # adr_ville_physique : Ville de l'adresse physique -
    adr_ville_physique = fields.TEXT(stored=True)
    # adr_rue_postale : Voie de l'adresse postale -
    adr_rue_postale = fields.TEXT(stored=True)
    # adr_rue_complement_postale : Complément de l'adresse postale -
    adr_rue_complement_postale = fields.TEXT(stored=True)
    # adr_code_postal_postale : Code postal de l'adresse postale -
    adr_code_postal_postale = fields.ID(stored=True)
    # adr_ville_postale : Ville de l'adresse postale
    adr_ville_postale = fields.TEXT(stored=True)


class DB(object):
    '''
    Data storage abstraction layer
    '''
    searched_fields = ['da_raison_sociale', 'da_siren', 'numero_de_da', 'da_no_etab']

    def __init__(self, config):
        self.config = config
        self.schema = Organization()
        if not os.path.exists(config.index):
            os.mkdir(config.index)
        if index.exists_in(config.index):
            self.index = index.open_dir(config.index)
        else:
            self.index = index.create_in(config.index, self.schema)

    @contextmanager
    def indexing(self, max_memory=DEFAULT_MAX_MEMORY):
        nb_cpu = multiprocessing.cpu_count()
        memory = int(max_memory / nb_cpu)
        self.writer = self.index.writer(procs=nb_cpu, limitmb=memory, multisegment=True)
        yield {'cpus': nb_cpu, 'memcpu': memory, 'memory': max_memory}
        self.writer.commit(optimize=True)
        self.writer = None

    def save_organization(self, org):
        if not self.writer:
            log.error('You need to start indexing before saving organizations')
        fields = dict((k, v) for k, v in org.items() if k in self.schema)
        self.writer.add_document(**fields)

    def init_app(self, app):
        app.extensions['db'] = self

    def search(self, query, limit=10):
        qp = MultifieldParser(self.searched_fields, schema=self.index.schema)
        q = qp.parse(query)

        with self.index.searcher() as s:
            results = s.search(q, limit=limit)
            return {
                'query': query,
                'limit': limit,
                'total': results.scored_length(),
                'results': [hit.fields() for hit in results],
            }

    def get(self, identifier):
        with self.index.searcher() as s:
            for key in ('numero_de_da', 'da_siren'):
                doc = s.document(**{key: identifier})
                if doc:
                    return doc
