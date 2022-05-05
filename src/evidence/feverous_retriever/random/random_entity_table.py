from typing import List, Tuple
import numpy as np
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable

from ..utils import TableExceptionType, TableException


class RandomEntityTable:
    def __init__(self,
                 evidence_per_table,
                 columns_per_table,
                 rng: np.random.Generator,
                 ):
        self.rng = rng
        self.evidence_per_table = evidence_per_table
        self.columns_per_table = columns_per_table

    def entity_table(self,
                     tbl: WikiTable,
                     header_left: List[Tuple[str, int, str]],
                     ) -> Tuple[List[List[Cell]], List[Cell]]:
        """
        Extract the Evidences from the entity table i.e. from the header left

        :param tbl: one table present in the page
        :param header_left: list of tuple. Each element contains the first left header
        :param rng: random generator

        :return: the list of the selected cells and the content of the headers
        """
        # header_left [(header_cell, row_number, content), ... ]
        header_left = np.array(header_left)

        # Not enough rows
        if len(header_left) < self.columns_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

        selected_headers = self.rng.choice(header_left,
                                           self.columns_per_table,
                                           replace=False)

        # Now we need to select the cells from the selected headers
        rows = np.array(tbl.get_rows())
        i = selected_headers[:, 1].astype(int)

        selected_rows = rows[i]  # take only the selected row

        extracted_cell = []
        for r in selected_rows:

            unique_cells = [r.row[0]]
            for c in r.row[1:]:
                if c.content in [u.content for u in unique_cells]:
                    continue
                unique_cells.append(c)

            if len(unique_cells) - 1 < self.evidence_per_table:
                raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)

            cells = self.rng.choice(unique_cells[1:],
                               self.evidence_per_table,
                               replace=False)

            extracted_cell.append(cells)

        selected_content = np.transpose(extracted_cell)
        headers = selected_headers[:, 0]

        return selected_content, headers
