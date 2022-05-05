import transformers as ppb
import torch
from .claim_generator import TextualClaimGenerator


class FeverousGenerator(TextualClaimGenerator):
    """
    Generates TextualClaim objects using a t5-small model fine-tuned
    on a small part of the FEVEROUS dataset.
    The model was fine-tuned on strings encoded in 'compact' form.
    Different encodings may provide worse results.
    """

    def __init__(self,
                 encoding,
                 model_path,
                 verbose=False):
        super().__init__(encoding, verbose)
        self.tokenizer = ppb.T5Tokenizer.from_pretrained("t5-small")
        config = ppb.AutoConfig.from_pretrained("t5-small")
        self.model = ppb.T5ForConditionalGeneration(config)
        self.model.load_state_dict(torch.load(model_path,
                                              map_location=torch.device('cpu')))
        self.model.eval()

    def _generate_claim(self, text):
        input_ids = self.tokenizer.encode(text,
                                          add_special_tokens=True,
                                          truncation=True,
                                          return_tensors='pt'
                                          ).to(self.model.device)
        model_output = self.model.generate(input_ids)
        return self.tokenizer.decode(model_output[0])
