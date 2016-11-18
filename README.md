# OFSearch

Data loader and search API for french training organizations.

See [the official dataset documentation][of-dataset] for field explanation.


## Getting started

```shell
pip install -e .
ofsearch -v load ListeOF_20161116.xlsx
ofsearch serve
```

## Query

```shell
curl -s http://localhost:8888/organizations?q=wit | jq
```


[of-dataset]: https://www.data.gouv.fr/fr/datasets/liste-publique-des-organismes-de-formation-l-6351-7-1-du-code-du-travail/
