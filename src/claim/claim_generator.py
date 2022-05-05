from abc import abstractmethod
from logger import logger
from ..pipeline import PipelineElement
from .claim import TextualClaim


class TextualClaimGenerator(PipelineElement):
    """
    Element generating textual claims starting from Evidence objects.
    """

    def __init__(self, encoding, verbose=False):
        self.encoding = encoding
        self.verbose = False

    def generate(self, evidence):
        """
        Generate textual claims based on evidence

        :param evidence: a list of evidence objects
        :param verbose: if True prints additional debug informations
        :return: a list of TextualClaim objects
        """
        claims = []
        for i, e in enumerate(evidence):
            evidence_text = e.to_text(self.encoding)
            claim_text = self._generate_claim(evidence_text)
            claim_json = TextualClaimGenerator._evidence_to_json(i, e, claim_text)
            claim = TextualClaim(claim_text, e, claim_json)
            claims.append(claim)
            if self.verbose:
                logger.info(claim)
        return claims

    @abstractmethod
    def _generate_claim(self, text):
        """
        Given an encoded piece of Evidence generates
        the corresponding claim in textual form.
        Must be implemented in child class.

        :param text: encoded piece of Evidence
        :return: a claim in textual form
        """
        raise NotImplementedError("Must have implemented this.")

    # TODO: move this in claim.py
    @staticmethod
    def _evidence_to_json(sample_id,
                          evidence,
                          claim):
        """
        Encodes an Evidence object and its corresponding TextualClaim in JSON format

        :param sample_id:
        :param evidence:
        :param claim:
        :return: a dict object ready to be serialized
        """
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

    def __call__(self, *args, **kwargs):
        return self.generate(args[0])
