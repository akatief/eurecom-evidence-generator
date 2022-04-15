from abc import abstractmethod
from ..pipeline import PipelineElement
from .claim import TextualClaim


class TextualClaimGenerator(PipelineElement):
    """
    Element generating textual claims starting from Evidence objects.
    """

    def __init__(self, encoding):
        self.encoding = encoding

    def generate(self, evidence, header_content=False, verbose=False):
        """
        Generate textual claims based on evidence

        :param evidence: a list of evidence objects
        :param header_content: if True, insert the hedear information also in content
        :param verbose: if True prints additional debug informations
        :return: a list of TextualClaim objects
        """
        claims = []
        for i, e in enumerate(evidence):
            evidence_text = e.to_text(self.encoding)
            claim_text = self._generate_claim(evidence_text)
            claim_json = TextualClaimGenerator._evidence_to_json(i, e, claim_text,
                                                                 header_content)
            claim = TextualClaim(claim_text, e, claim_json)
            claims.append(claim)
            if verbose:
                print(claim)
        return claims

    @abstractmethod
    def _generate_claim(self, text):
        """
        Given an encoded piece of Evidence generates the corresponding claim in textual form.
        Must be implemented in child class.

        :param text: encoded piece of Evidence
        :return: a claim in textual form
        """
        raise NotImplementedError("Must have implemented this.")

    # TODO: move this in claim.py
    @staticmethod
    def _evidence_to_json(sample_id,
                          evidence,
                          claim,
                          header_content):
        """
        Encodes an Evidence object and its corresponding TextualClaim in JSON format

        :param sample_id:
        :param evidence:
        :param claim:
        :param header_content: boolean, if yes header present in the content
        :return: a dict object ready to be serialized
        """
        content = []
        context = {}
        for piece in evidence.evidence_pieces:
            key_h = f"{piece.wiki_page}_{piece.header.name}"
            key_c = f"{piece.wiki_page}_{piece.cell_id}"
            content.append(key_c)
            if header_content:
                content.append(key_c)

            context[key_c] = piece.context + [key_h]

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

    def __call__(self, *args, **kwargs):
        return self.generate(args[0])
