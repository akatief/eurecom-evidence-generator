import json
import hydra

from src.claim import TextualClaim
from src.claim import FeverousGenerator, ToTToGenerator

from src.pipeline import ClaimGeneratorPipeline
from src.evidence.feverous_retriever.random import FeverousRetrieverRandom
from src.evidence.feverous_retriever.entropy import FeverousRetrieverEntropy


# from src.evidence.feverous_retriever.entropy import FeverousRetrieverEntropy


@hydra.main(config_path="../src/config/", config_name="config_pipeline.yaml")
def main(cfg):
    retrievers = [FeverousRetrieverRandom(p_dataset=cfg.main.data_path,
                                          num_positive=cfg.positive_evidence,
                                          num_negative=cfg.negative_evidence,
                                          table_type=cfg.table_type,
                                          wrong_cell=cfg.wrong_cell,
                                          table_per_page=cfg.table_per_page,
                                          evidence_per_table=cfg.evidence_per_table,
                                          column_per_table=cfg.column_per_table,
                                          seed=cfg.seed,
                                          verbose=True,
                                          key_strategy=strat
                                          )
                  # for strat in ['entity', 'random']
                  for strat in ['random']
                  ]

    generator1 = FeverousGenerator(encoding='compact',
                                   model_path=cfg.main.model_path, )

    # generator2 = ToTToGenerator(
    # encoding='totto', model_path=cfg.main.model_path
    # )
    # generator3 = ToTToGenerator(encoding='compact',
    #                             model_path=cfg.main.model_path,
    #                             verbose=True)
    # generator = ToTToGenerator(encoding='totto',
    #                            model_path=cfg.main.model_path)

    generators = [generator1]

    pipeline = ClaimGeneratorPipeline([retrievers, generators])

    claims = pipeline.generate()

    json_evidence = TextualClaim.to_json(claims)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(json_evidence, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
