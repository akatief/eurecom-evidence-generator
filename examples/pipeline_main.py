import hydra
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage

from claim import FeverousGenerator
from pipeline import ClaimGeneratorPipeline
from src.evidence import FeverousRandomRetriever


@hydra.main(config_path="../src/config/", config_name="config_pipeline.yaml")
def main(cfg):
    db = FeverousDB(cfg.main.data_path)
    page_id = '1889 Liverpool City Council election'
    page_json = db.get_doc_json(page_id)
    wiki_page = WikiPage(page_id, page_json)

    # wiki_tables = wiki_page.get_tables()  # return list of all Wiki Tables
    # print(wiki_tables[8].all_cells)
    # print(wiki_tables[8])

    # class_feverous = FeverousRandomRetriever(cfg.data_path_main,
    #                                          cfg.num_evidence,
    #                                          cfg.n_pieces,
    #                                          cfg.table_per_page,
    #                                          cfg.evidence_per_table,
    #                                          cfg.column_per_table,
    #                                          cfg.seed
    #                                          )
    #
    # rng = np.random.default_rng(cfg.seed)

    retriever = FeverousRandomRetriever(cfg.main.data_path,
                                        cfg.num_evidence,
                                        cfg.table_per_page,
                                        cfg.evidence_per_table,
                                        cfg.column_per_table,
                                        cfg.seed
                                        )
    generator = FeverousGenerator(cfg.main.model_path)

    pipeline = ClaimGeneratorPipeline([retriever, generator])
    output, text_evidence = pipeline.generate(
        None)  # Right now, FeverousRetriever doesn't support an input table

    # output, text_evidence = generator.generate(output)

    for i, (o, e) in enumerate(zip(output, text_evidence)):
        print()
        print(f'Claim {i}: ')
        print('Generated: ', o)
        print('Evidence : ', e)
        

if __name__ == '__main__':
    main()
