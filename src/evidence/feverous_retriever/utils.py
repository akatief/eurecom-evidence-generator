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
            # TODO: different level of header_cell on the left
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
                             type_table: str
                             ) -> List[Evidence]:
    """
    It takes as argument the List of EvidencePieces. Each element of the list contains
    the list of evidence pieces extracted from one table.
    It returns the list of Evidence object created from each set of EvidencePieces.
    :param evidence_from_table: each element is [EvidencePiece] got from the table
    :param wrong_cell: how many cells are swapped to create REFUTED evidences
    :param rng: used to randomly swap the cells
    :param type_table: evidence extracted from table ['entity','relational']

    :return: list of REFUTED Evidences
    """
    negative_evidences = []
    for evidence_pieces in evidence_from_table:
        # evidence_pieces: list of evidence pieces from one table
        # the row already presents
        present_rows = set([piece.row for piece in evidence_pieces])
        # the columns already presents
        present_cols = set([piece.column for piece in evidence_pieces])

        if len(present_rows) > 1:  # entity table
            already_present = list(present_cols)
            tbl_type = 'entity'
        else:  # relational table
            already_present = list(present_rows)
            tbl_type = 'relational'

        # if there are not enough cells to swap throw an exception
        if len(evidence_pieces) < wrong_cell:
            raise TableException(
                TableExceptionType.NO_NEGATIVE_SENT,
                evidence_pieces[0].wiki_page
            )

        # randomly select which of the cells has to be swapped
        pieces_replace = rng.choice(len(evidence_pieces),
                                    wrong_cell,
                                    replace=False)

        # for each selected cell make the swap
        for p in pieces_replace:
            # if not enough possible pieces raise error
            if len(evidence_pieces[p].possible_pieces) <= 1:
                raise TableException(
                    TableExceptionType.NO_NEGATIVE_SENT,
                    evidence_pieces[p].wiki_page
                )

            # shuffle the possible cells
            rng.shuffle(evidence_pieces[p].possible_pieces)

            # Select the cell to be swapped
            selected_cell = None
            for cell in evidence_pieces[p].possible_pieces:
                # if the selected cell not already present
                # is -1 in the case the cell is empty
                if cell != -1 \
                        and cell.name != evidence_pieces[p].cell_id \
                        and not cell.is_header:
                    # Avoid possibility to randomly select same row/column
                    if tbl_type == 'relational' and cell.row_num not in already_present:
                        selected_cell = cell
                        already_present += [cell.row_num]
                        break
                    elif tbl_type == 'entity' and cell.col_num not in already_present:
                        selected_cell = cell
                        already_present += [cell.col_num]
                        break

            if selected_cell is None:
                raise TableException(
                    TableExceptionType.NO_NEGATIVE_SENT,
                    evidence_pieces[p].wiki_page
                )

            # Create the new SWAPPED evidence and insert the true in true_piece
            new_evidence = EvidencePiece(
                evidence_pieces[p].wiki_page,
                evidence_pieces[p].caption,
                selected_cell,
                evidence_pieces[p].header,
                evidence_pieces[p].possible_pieces,
                true_piece=evidence_pieces[p]
            )

            evidence_pieces[p] = new_evidence

        e = Evidence(evidence_pieces, "REFUTES", type_table)
        negative_evidences.append(e)

    return negative_evidences
