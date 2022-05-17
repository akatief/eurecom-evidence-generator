import numpy as np

from ..evidence import Evidence, EvidencePiece
from enum import Enum
from feverous.utils.wiki_page import WikiTable
from feverous.utils.wiki_table import Cell
from typing import List, Tuple

from logger import logger


class TableExceptionType(Enum):
    NO_HEADERS = 'NO_HEADERS'  # No headers in the table
    NO_ENOUGH_COL = 'NO_ENOUGH_COL'  # Not enough column in the header
    ID_NOT_COMPLIANT = 'ID_NOT_COMPLIANT'  # The id of the cell is not compliant
    SUBTABLE_NOT_FOUND = 'SUBTABLE_NOT_FOUND'  # Not possible to find a subtable
    NO_ENOUGH_ROW = 'NO_ENOUGH_ROW'  # Not enough row inside the subtable
    NO_ENOUGH_TBL = 'NO_ENOUGH_TBL'  # Not enough tbl inside the wikipage
    NO_EXTRACTED_TBL = 'NO_EXTRACTED_TBL'  # Not enough valid table in the wikipage
    NO_NEGATIVE_SENT = 'NO_NEGATIVE_SENT'  # Not possible to extract negative sentence


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
                             column_per_table: int,
                             seed: int
                             ) -> List[Evidence]:
    """
    It takes as argument the List of EvidencePieces created from a specific table.
    It returns the list of Evidence object created from each set of EvidencePieces.

    :param seed:
    :type seed:
    :param column_per_table:
    :type column_per_table:
    :param evidence_from_table: each element is [EvidencePiece] got from the table

    :return positive_evidences: list containing the positive Evidence
    """
    positive_evidences = []
    for evidence_pieces in evidence_from_table:
        e = Evidence(
            evidence_pieces,  # List of all the evidence pieces which belong to the e
            column_per_table,
            "SUPPORTS",
            seed
        )
        positive_evidences.append(e)

    return positive_evidences


def create_negative_evidence(
        evidence_from_table: List[List[EvidencePiece]],
        wrong_cell: int,
        column_per_table: int,
        seed: int,
        rng: np.random.Generator
) -> List[Evidence]:
    negative_evidences = []
    for evidence_pieces in evidence_from_table:

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
                if cell.name != evidence_pieces[p].cell_id and not cell.is_header:
                    selected_cell = cell
                    break

            if selected_cell is None:
                raise TableException(
                    TableExceptionType.NO_NEGATIVE_SENT,
                    evidence_pieces[p].wiki_page
                )

            # Add in the caption the correct cell
            new_evidence = EvidencePiece(
                evidence_pieces[p].wiki_page,
                evidence_pieces[p].caption,
                selected_cell,
                evidence_pieces[p].header,
                evidence_pieces[p].possible_pieces,
                true_piece=evidence_pieces[p]
            )

            evidence_pieces[p] = new_evidence

        e = Evidence(
            evidence_pieces,  # List of all the evidence pieces which belong to the e
            column_per_table,
            "REFUTE",
            seed
        )
        negative_evidences.append(e)

    return negative_evidences
