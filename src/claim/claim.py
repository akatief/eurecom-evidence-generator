class TextualClaim:
    def __init__(self,
                 claim,
                 evidence,
                 json):
        """
        Initializes a TextualClaim object.

        :param claim: textual claim
        :param evidence: Evidence the claim was generated from
        :param json: Evidence in json format
        """
        self.claim = claim
        self.evidence = evidence
        self.json = json

    def __str__(self):
        return self.claim
