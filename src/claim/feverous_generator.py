import transformers as ppb
import torch
from .claim_generator import TextualClaimGenerator


class FeverousGenerator(TextualClaimGenerator):
    def __init__(self, model_path):
        super().__init__()
        self.tokenizer = ppb.T5Tokenizer.from_pretrained("t5-small")
        config = ppb.AutoConfig.from_pretrained("t5-small")
        self.model = ppb.T5ForConditionalGeneration(config)
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()

    def _evidence_to_text(self, evidence):
        '''
        Converts evidence objects into strings the model can elaborate to generate a textual claim

        :param evidence:
        :return:
        '''
        textual_pieces = [self._evidence_piece_to_text(ep) for ep in evidence.evidence_pieces]
        return ' | '.join(textual_pieces)

    def _evidence_piece_to_text(self,evidence_piece):
        data = [evidence_piece.content, evidence_piece.wiki_page, evidence_piece.header_content]
        return ' && '.join(data)

    def generate(self, evidence):
        textual_evidence = []
        textual_claims = []
        for e in evidence:
            text = self._evidence_to_text(e)
            textual_evidence.append(text)
            input_ids = self.tokenizer.encode(text, add_special_tokens=True, truncation=True, return_tensors='pt')\
                                      .to(self.model.device)
            outputs = self.model.generate(input_ids)
            gen_text = self.tokenizer.decode(outputs[0])
            textual_claims.append(gen_text)
        return textual_claims, textual_evidence
