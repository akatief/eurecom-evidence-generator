from typing import List, Tuple

import numpy as np
from feverous.utils.wiki_page import WikiTable
from feverous.utils.wiki_table import Cell

from ..utils import TableExceptionType, TableException


def entity_table(
        tbl: WikiTable,
        header_left: List[Cell],
        rng: np.random.Generator,
        column_per_table: int,
        evidence_per_table: int
) -> Tuple[
    List[List[Cell]],
    List[Cell],
    List[List[Cell]]
]:
    """
    Extract the Evidences from the entity table i.e. from the header left

    :param tbl: The table to be scanned
    :param header_left: list of header left cells
    :param rng: random generator
    :param column_per_table: how many cells for 1 Evidence
    :param evidence_per_table: how many Evidences from the same table

    :return selected_evidences: [ ['Totti', 128], ['Cassano', 103], ...]
    :return selected_h_cells: ['name', 'scored_gol']
    :return alternative_pieces: the swappable cells for each header
    """
    # header_left [(header_cell, row_number, content), ... ]
    header_left = np.array(header_left)

    # Not enough rows
    if len(header_left) < column_per_table:
        raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

    selected_h = rng.choice(header_left,
                            column_per_table,
                            replace=False)

    # Now we need to select the cells from the selected headers
    rows = np.array(tbl.get_rows())
    i = [int(h.row_num) for h in selected_h]

    selected_rows = rows[i]  # take only the selected row

    extracted_cell = []
    alternative_pieces = []
    for r in selected_rows:

        # Obtain first the unique cells form the entity table
        unique_cells = [r.row[0]]  # The first cell is the header
        for c in r.row[1:]:  # take all the other cells of the row
            if c.content in [u.content for u in unique_cells if u != -1]:
                unique_cells.append(-1)  # Not useful
            elif c.content == "":
                unique_cells.append(-1)  # Not useful
            elif c.is_header:
                unique_cells.append(-1)  # Not useful
            else:
                unique_cells.append(c)  # if everything ok, append the cell
        alternative_pieces.append(unique_cells[1:])

    alternative_pieces = np.array(alternative_pieces)

    # this masks contains the row that have all the cells to be extractable (no empty,...)
    mask = [(p != -1).all() for p in alternative_pieces.T]

    # mantain all the rows but keep only the correct column from which we can
    possible_cols = np.arange(0, alternative_pieces.shape[1])
    possible_cols = possible_cols[mask]  # remove not possible cell

    if len(possible_cols) < evidence_per_table:
        raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

        # Select from the unique cells the random extracted cell
    selected_col = rng.choice(possible_cols,
                              evidence_per_table,
                              replace=False)
    selected_evidences = alternative_pieces[:, selected_col].T

    return selected_evidences, selected_h, alternative_pieces
