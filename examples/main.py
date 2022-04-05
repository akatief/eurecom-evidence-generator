import hydra
import numpy as np
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage
from src.evidence import FeverousRandomRetriever


@hydra.main(config_path="../src/config/", config_name="config.yaml")
def main(cfg):
    print(type(cfg))
    db = FeverousDB(cfg.data_path)
    page_id = '1889 Liverpool City Council election'
    page_json = db.get_doc_json(page_id)
    wiki_page = WikiPage(page_id, page_json)

    # wiki_tables = wiki_page.get_tables()  # return list of all Wiki Tables
    # print(wiki_tables[8].all_cells)
    # print(wiki_tables[8])

    class_feverous = FeverousRandomRetriever(cfg.data_path,
                                             cfg.num_evidence,
                                             cfg.n_pieces,
                                             cfg.table_per_page,
                                             cfg.evidence_per_table,
                                             cfg.column_per_table,
                                             cfg.seed
                                             )

    rng = np.random.default_rng(cfg.seed)
    # evidences = class_feverous.get_evidence(wiki_tables[0],
    #                             [],
    #                             70,
    #                             rng=rng)
    #
    # print(evidences.shape)

    # selected_content, selected_h_cells = class_feverous.relational_table(wiki_tables[0],
    #                                                                      0,
    #                                                                      25,
    #                                                                      rng,
    #                                                                      True
    #                                                                      )
    # print(selected_content[0], '\n')
    # print(selected_h_cells[0], '\n')

    # Retrieve call is forwarded to parent class
    output = class_feverous.retrieve()
    # first_evidence = output[1]
    #
    # print(first_evidence)
    for i,o in enumerate(output):
        print(f'Evidence {i}: ', o)


if __name__ == '__main__':
    main()
