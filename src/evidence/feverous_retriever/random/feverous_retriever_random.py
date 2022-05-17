from typing import List, Tuple

import numpy as np
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable

from ...evidence import EvidencePiece
from ..feverous_retriever import FeverousRetriever
from .random_entity_table import entity_table
from .random_relational_table import relational_table
from ..utils import TableExceptionType, TableException


class FeverousRetrieverRandom(FeverousRetriever):
    def get_evidence_from_table(self,
                                tbl: WikiTable,
                                header_left: List[Tuple[str, int, str]],
                                table_len: int,
                                if_header=True,
                                rng=None) -> List[EvidencePiece]:
        """

          :param tbl: scanned table WikiTable
          :param header_left: list of tuple. Each element contains the first left header
          :param table_len: number of row in the table, scalar
          :param if_header: add or not add the header in the output Boolean
          :param rng: random numpy generator

          :return evidences: contains the list of evidences from this table
        """
        # returns multiple Row that are headers
        headers = tbl.get_header_rows()

        # no headers in the table
        if len(headers) == 0 and len(header_left) == 0:
            raise TableException(TableExceptionType.NO_HEADERS, tbl.page)

        if len(headers) != 0 and len(headers[0].row) <= self.column_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)

        try:
            output = self.random_strategy(tbl,
                                          header_left,
                                          table_len,
                                          if_header,
                                          rng)
        except TableException:
            raise

        selected_cells, selected_h_cells, possible_pieces = output
        evidences = []
        for evidence in selected_cells:
            local_evidences = []
            for i, c in enumerate(evidence):
                local_evidences.append(
                    EvidencePiece(tbl.page,
                                  tbl.caption,
                                  c,
                                  selected_h_cells[i],
                                  possible_pieces[i]
                                  )
                )

            evidences.append(np.array(local_evidences))

        return np.array(evidences)

    def random_strategy(
            self,
            tbl: WikiTable,
            header_left: List[Tuple[str, int, str]],
            table_len: int,
            if_header: bool,
            rng: np.random.Generator
    ) -> Tuple[
        List[List[Cell]],
        List[Cell],
        List[List[Cell]]
    ]:
        """
        It returns the list of evidences extracted from the table.
        the length of the list depends on "evidence_per_table"
        Example:
            selected_content = [['Totti', 128], ['Cassano', 103], ...]
            headers = ['name', 'scored_gol']

        :param tbl: one table present in the page
        :param header_left: list of tuple. Each element contains the first left header
        :param table_len: len of the table
        :param if_header: to insert or not the header
        :param rng: random generator for reproducibility

        :return: selected_content, headers
        """

        try:
            # Not header on the left
            if len(header_left) == 0:
                return relational_table(tbl,
                                        table_len,
                                        rng,
                                        self.evidence_per_table,
                                        self.column_per_table
                                        )
            else:
                return entity_table(tbl,
                                    header_left,
                                    rng,
                                    self.column_per_table,
                                    self.evidence_per_table
                                    )
        except TableException:
            raise
