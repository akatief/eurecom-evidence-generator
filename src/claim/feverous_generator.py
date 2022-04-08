import transformers as ppb
import torch
from .claim_generator import TextualClaimGenerator


class FeverousGenerator(TextualClaimGenerator):
    def __init__(self, model_path):
        super().__init__()
        self.tokenizer = ppb.T5Tokenizer.from_pretrained("t5-small")
        config = ppb.AutoConfig.from_pretrained("t5-small")
        self.model = ppb.T5ForConditionalGeneration(config)
        self.model.load_state_dict(torch.load(model_path,
                                              map_location=torch.device('cpu')))
        self.model.eval()

    def _evidence_to_text(self, evidence):
        """
        Converts evidence objects into strings the model can elaborate
        to generate a textual claim

        :param evidence:
        :return:
        """
        textual_pieces = [self._evidence_piece_to_text(ep)
                          for ep in evidence.evidence_pieces]
        return ' | '.join(textual_pieces)

    def _evidence_piece_to_text(self, evidence_piece):
        data = [evidence_piece.content,
                evidence_piece.wiki_page,
                evidence_piece.header_content]

        return ' && '.join(data)

    def _evidence_to_json(self,
                          sample_id,
                          evidence,
                          claim):
        content = []
        context = {}
        for piece in evidence.evidence_pieces:
            key_h = f"{piece.wiki_page}_{piece.header.name}"
            key_c = f"{piece.wiki_page}_{piece.cell_id}"
            content.append(key_h)
            content.append(key_c)
            context[key_h] = piece.header_content
            context[key_c] = piece.content

        evidence_json = {
            "id": sample_id,
            "label": evidence.label,
            "annotator_operations": [{
                "operation": "start",
                "value": "start",
                "time": "0"
            }],
            "evidence": [{
                "content": content,
                "context": context
            }],
            "claim": claim,
            "expected_challenge": "NumericalReasoning",
            "challenge": "NumericalReasoning"
        }

        return evidence_json

    def generate(self, evidence):
        textual_evidence = []
        textual_claims = []
        json_output = []
        for i, e in enumerate(evidence):
            text = self._evidence_to_text(e)
            textual_evidence.append(text)
            input_ids = self.tokenizer.encode(text, add_special_tokens=True,
                                              truncation=True, return_tensors='pt') \
                .to(self.model.device)
            outputs = self.model.generate(input_ids)
            gen_text = self.tokenizer.decode(outputs[0])
            textual_claims.append(gen_text)
            json_output.append(self._evidence_to_json(i, e, gen_text))

        return textual_claims, textual_evidence, json_output
