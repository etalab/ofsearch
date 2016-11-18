# OFSearch

Data loader and search API for french training organizations.

See [the official dataset documentation][of-dataset] for field explanation.

## Requirements

OFSearch requires Python 3

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

## Docker

Build image with:

```shell
docker build -t etalab/ofsearch .
```

or use the prebuilt image from Docker Hub:

```shell
docker pull etalab/ofsearch
```

Load data using:

```shell
docker run -it etalab/ofsearch load https://www.data.gouv.fr/s/resources/url/to/file.xlsx
```

You can know serve the data with:

```shell
docker run -it etalab/ofsearch
```


[of-dataset]: https://www.data.gouv.fr/fr/datasets/liste-publique-des-organismes-de-formation-l-6351-7-1-du-code-du-travail/
