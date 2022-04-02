class EvidencePiece:
    """
    Contains a single piece of information pertaining to some Evidence.
    """

    def __init__(self, wikipage, cell, header_cell):
        '''
        cell id => cell_<table_id>_<row_num>_<column_num>
        '''
        self.wiki_page = wikipage
        self.cell_id = cell.name
        self.table = cell.name.split('_')[1]
        self.row = cell.name.split('_')[2]
        self.column = cell.name.split('_')[3]
        self.header = header_cell

        # Added for the links in the table
        content = cell.content
        if len(content.split('|')) > 1:
            content = content.split('|')[1][:-2]
        self.content = content


class Evidence:
    '''
    Contains pieces of evidence along with the template giving meaning.
    '''

    def __init__(self,
                 evidence_pieces,
                 num_evidence,
                 table_per_page,
                 evidence_per_table,
                 column_per_table,
                 seed):
        '''
        :param evidence_pieces: List of List of pieces of evidence 
                                columns = sample header from the table
                                row = total number of evidence
                                 
        :param label: Defines the claim as either "SUPPORTS" or "REFUTES"
        :param template: The template with which the evidence was retrieved
        '''
        self.evidence_pieces = evidence_pieces
        self.evidence_pieces = evidence_pieces
        self.num_evidence = num_evidence
        self.table_per_page = table_per_page
        self.evidence_per_table = evidence_per_table
        self.column_per_table = column_per_table
        self.seed = seed
