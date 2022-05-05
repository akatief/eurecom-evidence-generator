from ..evidence import Evidence, EvidencePiece
from enum import Enum
from feverous.utils.wiki_page import WikiTable
from feverous.utils.wiki_table import Cell
from typing import List
from typing import Tuple

from logger import logger


class TableExceptionType(Enum):
    NO_HEADERS = 'NO_HEADERS'  # No headers in the table
    NO_ENOUGH_COL = 'NO_ENOUGH_COL'  # Not enough column in the header
    ID_NOT_COMPLIANT = 'ID_NOT_COMPLIANT'  # The id of the cell is not compliant
    SUBTABLE_NOT_FOUND = 'SUBTABLE_NOT_FOUND'  # Not possible to find a subtable
    NO_ENOUGH_ROW = 'NO_ENOUGH_ROW'  # Not enough row inside the subtable
    NO_ENOUGH_TBL = 'NO_ENOUGH_TBL'  # Not enough tbl inside the wikipage


class TableException(Exception):
    def __init__(self,
                 error: TableExceptionType,
                 wikipage: str):
        self.error = error, wikipage

        logger.error(f'got Error "{error}" for wikipage "{wikipage}"'.encode("utf-8"))


def check_header_left(tbl: WikiTable
                      ) -> \
        Tuple[
            List[Tuple[Cell, int, str]],
            int
        ]:
    """
    it scans all the rows to check if header on the left are present.
    If present, it returns a list of tuple where each tuple contains
     ( header_cell, header_row, header_content )

    :param tbl: table to be scanned WikiTable

    :return header_index: list of tuple (header_cell, row_number, content)
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
                    (first_cell, int(row.row_num), first_cell.content)
                )

    return header_index, len(rows)


def create_positive_evidence(evidence_from_table: List[List[EvidencePiece]],
                             ) -> List[Evidence]:
    """
    It takes as argument the List of EvidencePieces created from a specific table.
    It returns the list of Evidence object created from each set of EvidencePieces.

    :param seed:
    :param column_per_table:
    :param evidence_from_table: each element is [EvidencePiece] got from the table

    :return positive_evidences: list containing the positive Evidence
    """
    positive_evidences = []
    for evidence_piece in evidence_from_table:
        positive_evidences.append(
            Evidence(
                evidence_piece,
                "SUPPORTS"
            )
        )

    return positive_evidences


def create_negative_evidence():
    # TODO: implement_negative_evidence
    pass
