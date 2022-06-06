import json
import hydra

# TODO: try to understand because if it is not used you get error
import tensorflow_text

from src.claim import TextualClaim
from src.claim import FeverousGenerator, ToTToGenerator

from src.pipeline import ClaimGeneratorPipeline
from src.evidence.feverous_retriever.random import FeverousRetrieverRandom



@hydra.main(config_path="../src/config/", config_name="config_pipeline.yaml")
def main(cfg):
    retrievers = [FeverousRetrieverRandom(p_dataset=cfg.main.data_path,
                                          num_positive=cfg.positive_evidence,
                                          num_negative=cfg.negative_evidence,
                                          wrong_cell=cfg.wrong_cell,
                                          table_per_page=cfg.table_per_page,
                                          evidence_per_table=cfg.evidence_per_table,
                                          column_per_table=cfg.column_per_table,
                                          seed=cfg.seed,
                                          key_strategy=strat,
                                          verbose=True
                                          )
                  # for strat in ['entity', 'random']
                  for strat in ['entity']
                  ]

    generator1 = FeverousGenerator(encoding='totto',
                                   model_path=cfg.main.model_path,)

    generator2 = ToTToGenerator(
    encoding='totto', model_path='../models/exported_totto_large/1648208035'
    )
    generator3 = ToTToGenerator(encoding='compact',
                                model_path=cfg.main.model_path,
                                verbose=True)
    generator = ToTToGenerator(encoding='totto',
                               model_path=cfg.main.model_path)

    generators = [generator2]

    pipeline = ClaimGeneratorPipeline([retrievers, generators])

    # Right now, FeverousRetriever doesn't support an input table
    claims = pipeline.generate()

    json_evidence = TextualClaim.to_json(claims)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(json_evidence, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
