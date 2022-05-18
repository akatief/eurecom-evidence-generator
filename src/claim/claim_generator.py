from abc import abstractmethod
from logger import logger
from pipeline import PipelineElement
from .claim import TextualClaim


class TextualClaimGenerator(PipelineElement):
    """
    Element generating textual claims starting from Evidence objects.
    """

    def __init__(self, encoding, verbose=False):
        self.encoding = encoding
        self.verbose = verbose

    def generate(self, evidence):
        """
        Generate textual claims based on evidence

        :param evidence: a list of evidence objects
        :return: a list of TextualClaim objects
        """
        claims = []
        for i, e in enumerate(evidence):
            evidence_text = e.to_text(self.encoding)
            if self.verbose:
                logger.info(evidence_text)
            claim_text = self._generate_claim(evidence_text)
            claim = TextualClaim(claim_text, e)
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


    def __call__(self, *args, **kwargs):
        return self.generate(args[0])
