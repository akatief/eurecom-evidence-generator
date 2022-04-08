import hydra
import numpy as np
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage
from evidence import FeverousRandomRetriever


@hydra.main(config_path="../src/config/", config_name="config_pipeline.yaml")
def main(cfg):
    db = FeverousDB(cfg.main.data_path)
    page_id = '1889 Liverpool City Council election'
    page_json = db.get_doc_json(page_id)
    wiki_page = WikiPage(page_id, page_json)

    wiki_tables = wiki_page.get_tables()  # return list of all Wiki Tables

    print(wiki_page.get_page_items())
    # print([str(s) for s in wiki_page.get_sections()][19])

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


if __name__ == '__main__':
    main()
