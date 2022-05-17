class TextualClaim:
    #TODO: rename claim to text
    def __init__(self,
                 claim,
                 evidence):
        """
        Initializes a TextualClaim object.

        :param claim: textual claim
        :param evidence: Evidence the claim was generated from
        """
        self.claim = claim
        self.evidence = evidence

    def __str__(self):
        return self.claim

    @staticmethod
    def to_json(claims):
        """
        Convert a list of claims in json format

        :param claims: list of TextualClaim objects
        :return: a list of json-formatted claims
        """
        if not isinstance(claims,list):
            claims = [claims]
        jsons = []
        for i,c in enumerate(claims):
            jsons.append(TextualClaim._claim_to_json(i, c))
        return jsons

    @staticmethod
    def _claim_to_json(sample_id,
                          claim):
        """
        Encodes an Evidence object and its corresponding TextualClaim in JSON format

        :param sample_id: int id of the generated evidence
        :param claim: a TextualClaim object
        :return: a dict object ready to be serialized
        """
        content = []
        context = {}
        for piece in claim.evidence.evidence_pieces:
            key_h = f"{piece.wiki_page}_{piece.header.name}"
            key_c = f"{piece.wiki_page}_{piece.cell_id}"
            content.append(key_h)
            content.append(key_c)
            context[key_h] = piece.header_content
            context[key_c] = piece.content

        evidence_json = {
            "id": sample_id,
            "label": claim.evidence.label,
            "annotator_operations": [{
                "operation": "start",
                "value": "start",
                "time": "0"
            }],
            "evidence": [{
                "content": content,
                "context": context
            }],
            "claim": claim.claim,
            "expected_challenge": "NumericalReasoning",
            "challenge": "NumericalReasoning"
        }

        return evidence_json
