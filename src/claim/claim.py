class TextualClaim:
    # TODO: rename claim to text
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
        if not isinstance(claims, list):
            claims = [claims]
        jsons = []
        for i, c in enumerate(claims):
            jsons.append(TextualClaim._claim_to_json(i, c))
        return jsons

    # TODO: move this in claim.py
    @staticmethod
    def _claim_to_json(sample_id,
                       claim  # TextualClaim
                       ):
        """
        Encodes an Evidence object and its corresponding TextualClaim in JSON format

        :param sample_id:
        :param claim: TextualClaim containing all the information

        :return: json document for the claim
        """

        content = []  # list of content used as key in context
        context = {}  # for each content element, the associated context
        swapped = ''  # contains the swapped cell if REFUTED, otherwise -
        true = ''  # contains the true pieces

        # the evidence pieces used for generation the claim
        for piece in claim.evidence.evidence_pieces:
            if piece.true_piece is not None:  # REFUTED claim
                piece_json = piece.true_piece
                true += f'{piece_json.content}, {piece_json.cell_id} | '
                swapped += f'{piece.content}, {piece.cell_id} | '
            else:  # SUPPORTED claim
                piece_json = piece
                true += f'{piece_json.content}, {piece_json.cell_id} | '
                swapped += f'- | '

            # TODO: understand if header in the content
            key_h = f"{piece_json.wiki_page}_{piece_json.header.name}"
            # content.append(key_h)

            key_c = f"{piece_json.wiki_page}_{piece_json.cell_id}"
            content.append(key_c)

            context[key_c] = piece_json.caption + [key_h]

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
            "claim": str(claim),
            "true": true,
            "swapped": swapped,
            "table": claim.evidence.type_table,
            "expected_challenge": "Augumented",
            "challenge": "Augumented"
        }

        return evidence_json
