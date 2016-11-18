#!/usr/bin/env bash

SOURCE_URL="http://web.archive.org/web/20160114195407/https://www.listeof.travail.gouv.fr/index.php?module=Listeof&action=Recherche"
curl -s "$SOURCE_URL" | pup "select[name=specfor1] option:not([value=0]) json{}" | jq ".[].text" | sed 's/ - /;"/g' | sed 's/^"//g' | sed "s/&#39;/'/g"
