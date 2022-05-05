from .utils import clean_content
from .utils import to_totto_text
from .utils import to_compact_text


class EvidencePiece:
    """
    Contains a single piece of information pertaining to some Evidence.
    """

    def __init__(self, wikipage, caption, cell, header_cell):
        """
        cell id => cell_<table_id>_<row_num>_<column_num>
        """
        self.wiki_page = wikipage
        self.cell_id = cell.name
        self.cell = cell
        #TODO: error because some tables may have more headers on the left
        #  Universal Storage Platform, discontinued
        self.table = int(self.cell_id.split('_')[1])
        self.row = int(self.cell_id.split('_')[2])
        self.column = int(self.cell_id.split('_')[3])

        self.caption = caption

        self.header_content = clean_content(header_cell.content)
        self.header = header_cell

        # Added for the links in the table
        content = cell.content
        self.content = clean_content(content)

    def __str__(self):
        return f"{self.content} " \
               f"- {self.header_content} " \
               f"- {self.cell_id} -" \
               f" {', '.join([str(c) for c in self.caption])}"

    def __eq__(self, other):
        return self.cell_id == other.cell_id

    def __lt__(self, other):
        if self.wiki_page is not other.wiki_page:
            return self.wiki_page < other.wiki_page
        if self.table is not other.table:
            return self.table < other.table
        elif self.row is not other.row:
            return self.row < other.row
        elif self.column is not other.column:
            return self.column < other.column
        else:
            return False


class Evidence:
    """
    Contains pieces of evidence along with the template giving meaning.
    """

    def __init__(self,
                 evidence_pieces,
                 label):
        """
        :param evidence_pieces: List of List of pieces of evidence
                                columns = sample header from the table
                                row = total number of evidence
        :param label: Defines the claim as either "SUPPORTS" or "REFUTES"
        """
        self.evidence_pieces = evidence_pieces
        self.label = label

    def __str__(self):
        my_string = ''
        for e in self.evidence_pieces:
            my_string += f'{str(e)} | '

        return my_string + self.label

    def to_text(self, encoding='compact'):
        """
        Converts evidence objects into strings the model can elaborate
        to generate a textual claim.
        Uses selected encoding. Possible choices are 'compact' and 'totto'.

        :param encoding: encoding to use
        :return: text encoded in chosen form.
        """
        if encoding == 'compact':
            return to_compact_text(self.evidence_pieces)
        elif encoding == 'totto':
            return to_totto_text(self.evidence_pieces)
        else:
            raise ValueError('Invalid choice of encoding')
