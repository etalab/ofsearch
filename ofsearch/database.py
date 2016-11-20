import csv
import logging
import multiprocessing
import os
import pkg_resources

from contextlib import contextmanager

from whoosh import fields, index
from whoosh.analysis import NgramWordAnalyzer
from whoosh.qparser import MultifieldParser

log = logging.getLogger(__name__)


DEFAULT_INDEX = 'index'
DEFAULT_MAX_MEMORY = '1024'
MAX_SPECIALTIES = 15


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


schema = Organization()
# sf : Spécialité de Formation
schema.add('sf*', fields.NUMERIC(stored=True), glob=True)
# nsf : Nombre de stagiaires formés dans la spécialité
schema.add('nsf*', fields.NUMERIC(stored=True), glob=True)
# nhsf : Nombre d'heures-stagiaires suivies dans la spécialité
schema.add('nhsf*', fields.NUMERIC(stored=True), glob=True)


class DB(object):
    '''
    Data storage abstraction layer
    '''
    searched_fields = ['da_raison_sociale', 'da_siren', 'numero_de_da', 'da_no_etab']

    def __init__(self, config):
        self.config = config
        self.schema = schema
        if not os.path.exists(config.index):
            os.mkdir(config.index)
        if index.exists_in(config.index):
            self.index = index.open_dir(config.index)
        else:
            self.index = index.create_in(config.index, self.schema)
        self._specialties = None

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
        fields['form_total'] = parse_int(fields['form_total'])
        for i in range(1, MAX_SPECIALTIES + 1):
            sf_key = 'sf{0}'.format(i)
            nsf_key = 'nsf{0}'.format(i)
            nhsf_key = 'nhsf{0}'.format(i)
            sf = parse_int(fields.pop(sf_key, None))
            nsf = parse_int(fields.pop(nsf_key, None))
            nhsf = parse_int(fields.pop(nhsf_key, None))
            if not sf:
                continue
            fields[sf_key] = sf
            fields[nsf_key] = nsf
            fields[nhsf_key] = nhsf
        self.writer.add_document(**fields)

    def init_app(self, app):
        app.extensions['db'] = self

    def search(self, query, page=1, limit=10):
        qp = MultifieldParser(self.searched_fields, schema=self.index.schema)
        q = qp.parse(query)

        with self.index.searcher() as s:
            results = s.search_page(q, page, pagelen=limit)
            return {
                'query': query,
                'page': page,
                'limit': limit,
                'total': len(results),
                'results': [self.doc_to_org(hit.fields()) for hit in results],
            }

    def get(self, identifier):
        with self.index.searcher() as s:
            for key in ('numero_de_da', 'da_siren'):
                doc = s.document(**{key: identifier})
                if doc:
                    return self.doc_to_org(doc)

    def doc_to_org(self, doc):
        doc['specialties'] = []
        for i in range(1, MAX_SPECIALTIES + 1):
            sf_key = 'sf{0}'.format(i)
            nsf_key = 'nsf{0}'.format(i)
            nhsf_key = 'nhsf{0}'.format(i)
            sf = doc.pop(sf_key, None)
            nsf = doc.pop(nsf_key, None)
            nhsf = doc.pop(nhsf_key, None)
            if not sf:
                continue
            doc['specialties'].append({
                'code': sf,
                'trainees': nsf,
                'hours': nhsf,
            })
        return doc

    @property
    def specialties(self):
        if not self._specialties:
            with open(pkg_resources.resource_filename(__name__, 'specialties.csv')) as csvfile:
                reader = csv.reader(csvfile, delimiter=';', quotechar='"')
                self._specialties = dict(reader)
        return self._specialties
