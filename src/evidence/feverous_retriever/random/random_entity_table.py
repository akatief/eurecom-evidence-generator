from typing import List, Tuple
import numpy as np
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable

from ..utils import TableExceptionType, TableException

# TODO: use Cell header_left to get directly id and content
#  instead of passing a tuple
def entity_table(
        tbl: WikiTable,
        header_left: List[Tuple[Cell, int, str]],
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

    :param evidence_per_table:
    :param column_per_table:
    :param tbl: one table present in the page
    :param header_left: list of tuple. Each element contains the first left header
    :param rng: random generator
    :return: the list of the selected cells and the content of the headers
    """
    # header_left [(header_cell, row_number, content), ... ]
    header_left = np.array(header_left)

    # Not enough rows
    if len(header_left) < column_per_table:
        raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

    selected_headers = rng.choice(header_left,
                                  column_per_table,
                                  replace=False)

    # Now we need to select the cells from the selected headers
    rows = np.array(tbl.get_rows())
    i = selected_headers[:, 1].astype(int)

    selected_rows = rows[i]  # take only the selected row

    extracted_cell = []
    possible_pieces = []
    for r in selected_rows:

        # Obtain first the unique cells form the entity table
        unique_cells = [r.row[0]]  # The first cell is the header
        for c in r.row[1:]:  # take all the other cells of the row
            if c.content in [u.content for u in unique_cells]:
                continue
            if c.is_header:
                continue

            unique_cells.append(c)

        if len(unique_cells) - 1 < evidence_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)

        possible_pieces.append(unique_cells)

        # Select from the unique cells the random extracted cell
        cells = rng.choice(unique_cells[1:],
                           evidence_per_table,
                           replace=False)

        extracted_cell.append(cells)

    # TODO: maybe change function to remove numpy dependence
    selected_content = np.transpose(extracted_cell).tolist()
    headers = selected_headers[:, 0]
    # TODO: fix typing
    return selected_content, headers, possible_pieces
