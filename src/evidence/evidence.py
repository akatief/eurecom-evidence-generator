class EvidencePiece:
    '''
    Contains a single piece of information pertaining to some Evidence.
    '''
    def __init__(self,
            table, row, column):
        '''
        :param table: Table containing the evidence piece
        :param row: Row containing the evidence piece
        :param column: Column containing the evidence piece
        '''
        self.table = table
        self.row = row
        self.column = column
        self.content = table[row, column]

class Evidence:
    '''
    Contains pieces of evidence along with the template giving meaning.
    '''
    def __init__(self,
            evidence_pieces,
            label,
            template):
        '''
        :param evidence_pieces: List of pieces of evidence composing the claim.
        :param label: Defines the claim as either "SUPPORTS" or "REFUTES"
        :param template: The template with which the evidence was retrieved
        '''
        self.evidence_pieces = evidence_pieces
        self.label = label
        self.template = template