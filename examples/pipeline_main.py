import json

import hydra

# TODO: try to understand because if it is not used you get error
import tensorflow_text

from src.claim import FeverousGenerator, ToTToGenerator

from src.pipeline import ClaimGeneratorPipeline
from src.evidence import FeverousRetrieverRandom


@hydra.main(config_path="../src/config/", config_name="config_pipeline.yaml")
def main(cfg):
    retriever = FeverousRetrieverRandom(cfg.main.data_path,
                                        cfg.positive_evidence,
                                        cfg.negative_evidence,
                                        cfg.wrong_cell,
                                        cfg.table_per_page,
                                        cfg.evidence_per_table,
                                        cfg.column_per_table,
                                        cfg.seed,
                                        cfg.verbose,
                                        )

    generator = FeverousGenerator(encoding='compact',
                                  model_path=cfg.main.model_path)
    #
    # generator = ToTToGenerator(encoding='totto',
    #                            model_path=cfg.main.model_path)

    pipeline = ClaimGeneratorPipeline([retriever, generator])
    claims = pipeline.generate(
        None,  # Right now, FeverousRetriever doesn't support an input table
        header_content=cfg.header_content)
    json_evidence = [c.json for c in claims]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(json_evidence, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
