import numpy as np
from ..evidence import Evidence
from ..evidence import EvidencePiece
from enum import Enum
from feverous.utils.wiki_page import WikiTable
from feverous.utils.wiki_table import Cell
from typing import List
from typing import Tuple

from ...logger import logger


class TableExceptionType(Enum):
    # Possible Errors inside the code
    NO_HEADERS = 'NO_HEADERS'  # No headers in the table
    NO_ENOUGH_COL = 'NO_ENOUGH_COL'  # Not enough column in the header
    ID_NOT_COMPLIANT = 'ID_NOT_COMPLIANT'  # The id of the cell is not compliant
    SUBTABLE_NOT_FOUND = 'SUBTABLE_NOT_FOUND'  # Not possible to find a subtable
    NO_ENOUGH_ROW = 'NO_ENOUGH_ROW'  # Not enough row inside the subtable
    NO_ENOUGH_TBL = 'NO_ENOUGH_TBL'  # Not enough tbl inside the wikipage
    NO_EXTRACTED_TBL = 'NO_EXTRACTED_TBL'  # Not enough valid table in the wikipage
    NO_NEGATIVE_SENT = 'NO_NEGATIVE_SENT'  # Not possible to extract negative sentence


class TableException(Exception):
    """Class to handle the possible errors"""

    def __init__(self,
                 error: TableExceptionType,
                 wikipage: str):
        self.error = error, wikipage

        logger.error(f'got Error "{error}" for wikipage "{wikipage}"'.encode("utf-8"))


def check_header_left(tbl: WikiTable
                      ) -> Tuple[List[Cell], int]:
    """
    it scans all the rows to check if header on the left are present.
    If present, it returns a list of header cells.

    :param tbl: table to be scanned WikiTable

    :return header_index: list of left header_cell
    :return count: number of rows in the table
    """
    header_index = []
    rows = tbl.get_rows()
    for row in rows:
        if row.is_header_row():
            continue

        else:

            first_cell = row.get_row_cells()[0]
            if first_cell.is_header:
                header_index.append(
                    first_cell
                    # (first_cell, int(row.row_num), first_cell.content)
                )

    return header_index, len(rows)


def create_positive_evidence(evidence_from_table: List[List[EvidencePiece]],
                             type_table: str
                             ) -> List[Evidence]:
    """
    It takes as argument the List of EvidencePieces. Each element of the list contains
    the list of evidence pieces extracted from one table.
    It returns the list of Evidence object created from each set of EvidencePieces.


    :param evidence_from_table: each element is [EvidencePiece] got from the table
    :param type_table: evidence extracted from table ['entity','relational']

    :return positive_evidences: list containing the positive Evidence
    """
    positive_evidences = []
    for evidence_pieces in evidence_from_table:
        e = Evidence(evidence_pieces, "SUPPORTS", type_table)
        positive_evidences.append(e)

    return positive_evidences


def create_negative_evidence(evidence_from_table: List[List[EvidencePiece]],
                             wrong_cell: int,
                             rng: np.random.Generator,
                             tbl: WikiTable,
                             type_table: str
                             ) -> List[Evidence]:
    """
    It takes as argument the List of EvidencePieces. Each element of the list contains
    the list of evidence pieces extracted from one table.
    It returns the list of Evidence object created from each set of EvidencePieces.
    :param evidence_from_table: each element is [EvidencePiece] got from the table
    :param wrong_cell: how many cells are swapped to create REFUTED evidences
    :param rng: used to randomly swap the cells
    :param tbl: WikiTable: the table from which we habve extracted the evidences
    :param type_table: evidence extracted from table ['entity','relational']

    :return: list of REFUTED Evidences
    """
    negative_evidences = []
    for evidence_pieces in evidence_from_table:
        # evidence_pieces: list of evidence pieces from one table
        # the row already presents
        if type_table == 'entity':
            # these are the columns already present int the evidence pieces
            # when swap we not both element on the same column
            already_present = list(set([piece.column for piece in evidence_pieces]))

        if type_table == 'relational':
            already_present = list(set([piece.row for piece in evidence_pieces]))

        # randomly select which of the cells has to be swapped
        pieces_replace_row = rng.choice(len(evidence_pieces),
                                        wrong_cell,
                                        replace=False)

        # for each selected cell make the swap
        for i in pieces_replace_row:
            # if not enough possible pieces raise error
            # -1 because no possible cell (empty)
            p = evidence_pieces[i]
            p.possible_pieces = np.array(p.possible_pieces)
            if len(p.possible_pieces[p.possible_pieces != -1]) < 1:
                raise TableException(
                    TableExceptionType.NO_NEGATIVE_SENT,
                    p.wiki_page
                )

            # shuffle the possible cells
            # TODO: check possible error in entity for possible pieces
            rng.shuffle(p.possible_pieces)

            # Select the cell to be swapped
            selected_cell = None
            for cell in p.possible_pieces:
                # if the selected cell not already present
                # is -1 in the case the cell is empty
                if _check_cell_swap(cell, p, tbl):
                    # Avoid possibility to randomly select same row/column
                    if type_table == 'relational' and cell.row_num not in already_present:
                        already_present += [cell.row_num]
                    elif type_table == 'entity' and cell.col_num not in already_present:
                        already_present += [cell.col_num]
                    selected_cell = cell
                    break

            if selected_cell is None:
                raise TableException(
                    TableExceptionType.NO_NEGATIVE_SENT,
                    p.wiki_page
                )

            # Create the new SWAPPED evidence and insert the true in true_piece
            new_evidence = EvidencePiece(
                p.wiki_page,
                p.caption,
                selected_cell,
                p.header,
                p.possible_pieces,
                true_piece=p
            )

            evidence_pieces[i] = new_evidence

        e = Evidence(evidence_pieces, "REFUTES", type_table)
        negative_evidences.append(e)

    return negative_evidences


def _check_cell_swap(possible_swap: Cell, piece: EvidencePiece, tbl: WikiTable):
    """ controls whether the possible swap cell is valid to swap"""
    if possible_swap == -1:  # contains empty
        return False
    if possible_swap.name == piece.cell_id:
        return False
    if possible_swap.is_header:
        return False
    if sum([1 for c in tbl.all_cells if piece.content == tbl.get_cell(c).content]) > 1:
        return False  # return False if the cell is present twice in the table

    return True
