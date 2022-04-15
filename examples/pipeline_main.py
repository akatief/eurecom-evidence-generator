import json

import hydra
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage

from src.pipeline import ClaimGeneratorPipeline
from src.evidence import FeverousRandomRetriever
from src.claim import FeverousGenerator
import numpy as np
import os


@hydra.main(config_path="../src/config/", config_name="config_pipeline.yaml")
def main(cfg):
    """
    db = FeverousDB(cfg.main.data_path)
    page_id = '1889 Liverpool City Council election'
    page_json = db.get_doc_json(page_id)
    wiki_page = WikiPage(page_id, page_json)

    wiki_tables = wiki_page.get_tables()  # return list of all Wiki Tables

    # print(wiki_page.get_page_items())
    # print([str(s) for s in wiki_page.get_sections()][19])
    print(wiki_page.get_context('table_caption_19'))
    print([s.get_id() for s in wiki_page.get_context('table_caption_19')])
    print([str(s) for s in wiki_page.get_context('table_caption_19')])

    print(wiki_tables[19].get_table_caption())

    rng = np.random.default_rng(cfg.seed)

    retriever = FeverousRandomRetriever(cfg.main.data_path,
                                        cfg.num_evidence,
                                        cfg.table_per_page,
                                        cfg.evidence_per_table,
                                        cfg.column_per_table,
                                        cfg.seed
                                        )

    evidences = retriever.retrieve()

    for i, e in enumerate(evidences):
        print(f'=========== Evidence {i} ========')
        print(e, '\n')
    """

    retriever = FeverousRandomRetriever(cfg.main.data_path,
                                        num_evidence=cfg.num_evidence,
                                        table_per_page=cfg.table_per_page,
                                        evidence_per_table=cfg.evidence_per_table,
                                        column_per_table=cfg.column_per_table,
                                        seed=cfg.seed
                                        )
    generator = FeverousGenerator(encoding='compact',
                                  model_path=cfg.main.model_path)

    # generator = ToTToGenerator(encoding='totto',
    #                           model_path=cfg.main.model_path)

    pipeline = ClaimGeneratorPipeline([retriever, generator])
    claims = pipeline.generate(
        None, # Right now, FeverousRetriever doesn't support an input table
        header_content=cfg.header_content)
    json_evidence = [c.json for c in claims]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(json_evidence, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
