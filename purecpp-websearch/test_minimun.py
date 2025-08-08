from purecpp_websearch.websearch import WebSearch
ws = WebSearch(provider="brave", cleaner="simple")

payload = ws.search_and_read_structured(
    "Bolsonaro foi preso?",
    k=3,
    lang="en",
    ui_lang="en-US",
    country="US",
    freshness="pm",
    mime="text/html",
    include_raw_html=False,   # true se quiser salvar o HTML original no metadata
)

import json
print(json.dumps(payload, ensure_ascii=False, indent=2)[:2000])
