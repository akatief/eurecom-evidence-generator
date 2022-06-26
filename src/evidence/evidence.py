from typing import List
from typing import Union
from feverous.utils.wiki_table import Cell
from .utils import clean_content
from .utils import get_context




class EvidencePiece:
    """
    One single Evidence Piece. Multiple evidence pieces create an Evidence.
    """
    # TODO: add argument comments
    def __init__(self,
                 wikipage: str,
                 caption: List,
                 cell: Cell,
                 header_cell: Cell,
                 possible_pieces: List[Cell],
                 true_piece: Union[None, 'EvidencePiece'] = None):
        """
        :param wikipage: Name of the wikipage that contains this piece
        :param caption: contain the title/sections table for the piece
        :param cell: the extracted cell
        :param header_cell: the associated header cell
        :param possible_pieces: the possible pieces to swap for creating negative sentence
        :param true_piece: None if SUPPORT, The correct EvidencePiece if REFUTES
        """
        self.true_piece = true_piece  # it contains the ture EvidencePiece if necessary
        self.possible_pieces = possible_pieces  # Contains the possible rows

        self.wiki_page = wikipage  # the WikiPage name
        self.cell_id = cell.name  # the id of the cells

        # TODO: error because some tables may have more headers on the left
        #  Universal Storage Platform, discontinued
        self.table = int(self.cell_id.split('_')[1])
        self.row = int(self.cell_id.split('_')[2])
        self.column = int(self.cell_id.split('_')[3])

        # contains the title and the sections of the table
        self.caption = get_context(caption, wikipage)

        self.cell = cell  # The object Cell
        self.content = clean_content(cell.content)  # The str content

        self.header = header_cell  # The cell Header
        self.header_content = clean_content(header_cell.content)  # the str header content

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


# TODO: add argument comments
class Evidence:
    """
    It is the Evidence used to generate the sentence
    """

    def __init__(self,
                 evidence_pieces: List[EvidencePiece],
                 label: str,
                 type_table: str):
        """
        :param evidence_pieces: contain the EvidencePieces used in this Evidence
        :param label: Defines the claim as either "SUPPORTS" or "REFUTES"
        :param type_table: evidence extracted from table ['entity','relational']

        """
        self.evidence_pieces = evidence_pieces
        self.label = label
        self.type_table = type_table

    def __str__(self):
        my_string = ''
        for e in self.evidence_pieces:
            my_string += f'{str(e)} | '

        return my_string + self.label

    def to_text(self,
                encoding: str = 'compact'):
        """
        Converts evidence objects into strings the model can elaborate
        to generate a textual claim.
        Uses selected encoding. Possible choices are 'compact' and 'totto'.

        :param encoding: encoding to use
        :return: text encoded in chosen form.
        """
        if encoding == 'compact':
            return self.to_compact_text()
        elif encoding == 'totto':
            return self.to_totto_text()
        else:
            raise ValueError('Invalid choice of encoding')

    # TODO: solve circular dependency
    def to_compact_text(self):
        """
        Converts evidence objects into strings the model can elaborate to generate
         a textual claim

        :return: text encoded in compact form.
                 eg:
                 'Washington && City && List of cities
                 | 7.615 millions && Inhabitants && List of cities '
        """
        ep_to_text = lambda ep: ' && '.join([ep.content, ep.wiki_page, ep.header_content])
        textual_pieces = [ep_to_text(ep) for ep in self.evidence_pieces]
        return ' | '.join(textual_pieces)

    # TODO: solve circular dependency
    def to_totto_text(self):
        """
        Converts evidence objects into strings
        the model can elaborate to generate a textual claim

        :return: text encoded in totto form.
                 eg: <page_title> list of governors of south carolina </page_title>
                  <section_title> governors under the constitution of 1868 </section_title>
                  <table> <cell> 76 </cell>
                  <cell> daniel henry chamberlain </cell>
                  <cell> december 1, 1874 </cell> </table>
        """
        pieces = self.evidence_pieces
        pieces.sort()

        t_start = '<table> '
        t_end = ' </table>'
        r_start = '<row> '
        r_end = ' </row>'
        c_start = ' <cell> '
        c_end = ' </cell>'
        h_start = ' <col_header> '
        h_end = ' </col_header> '
        title = ' <page_title> ' + pieces[0].wiki_page + ' </page_title> '

        # TODO: implement better management for title
        #  (eg: print every unique title across all EvidencePieces)
        text = title + t_start + r_start + c_start
        curr_table = pieces[0].table
        curr_row = pieces[0].row
        curr_column = pieces[0].column

        for p in pieces:
            if p.table != curr_table:
                text += c_end + r_end + t_end + t_start + r_start + c_start
                curr_table = p.table
                curr_row = p.row
                curr_column = p.column
            elif p.row != curr_row:
                text += c_end + r_end + r_start + c_start
                curr_row = p.row
                curr_column = p.column
            elif p.column != curr_column:
                text += c_end + c_start
                curr_column = p.column
            text += p.content + h_start + p.header_content + h_end

        text += c_end + r_end + t_end
        return text