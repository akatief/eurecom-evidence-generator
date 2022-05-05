from typing import List, Tuple
import numpy as np
from numpy import ndarray
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable

from ...evidence import EvidencePiece
from ..feverous_retriever import FeverousRetriever
from .random_entity_table import RandomEntityTable
from .random_relational_table import RandomRelationalTable
from ..utils import TableExceptionType, TableException


class FeverousRetrieverRandom(FeverousRetriever):
    def __init__(self,
                 p_dataset: str,
                 num_evidence: int,
                 table_per_page=1,
                 evidence_per_table=1,
                 column_per_table=2,
                 key_strategy=None,
                 seed=None,
                 verbose=False):
        super().__init__(p_dataset, num_evidence, table_per_page, evidence_per_table, column_per_table, seed, verbose)
        self.key_strategy = key_strategy

    def get_evidence_from_table(self,
                                tbl: WikiTable,
                                header_left: List[Tuple[str, int, str]],
                                table_len: int):
        """
        it is used to extract the "meaningful" attributes from one table at time.
        "Meaningful" is defined by the target application.

        Example:
              evidences = [
                  [
                      EvidencePiece('Totti', 'name'),
                      EvidencePiece(128, 'scored_gol)
                  ],
                  [...],
                  ...
              ]

        :param tbl: scanned table WikiTable
        :param header_left: list of tuple. Each element contains the first left header
        :param table_len: number of row in the table, scalar

        :return: evidences: contains the list of evidences from this table
        """
        # returns multiple Row that are headers
        headers = tbl.get_header_rows()

        # no headers in the table
        if len(headers) == 0 and len(header_left) == 0:
            raise TableException(TableExceptionType.NO_HEADERS, tbl.page)

        if len(headers) != 0 and len(headers[0].row) < self.column_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)

        try:
            output = self.random_strategy(tbl,
                                          header_left,
                                          table_len)
        except TableException:
            raise

        selected_cells, selected_h_cells = output
        evidences = []
        for evidence in selected_cells:
            local_evidences = []
            for header_cell, cell in zip(selected_h_cells,evidence):
                local_evidences.append(EvidencePiece(tbl.page,
                                                     tbl.caption,
                                                     cell,
                                                     header_cell))

            evidences.append(local_evidences)

        return evidences

    def random_strategy(self,
                        tbl: WikiTable,
                        header_left: List[Tuple[str, int, str]],
                        table_len: int,
                        ) -> Tuple[List[List[Cell]], List[Cell]]:
        """
        It returns the list of evidences extracted from the table.
        the length of the list depends on "evidence_per_table"
        Example:
            selected_content = [['Totti', 128], ['Cassano', 103], ...]
            headers = ['name', 'scored_gol']

        :param tbl: one table present in the page
        :param header_left: list of tuple. Each element contains the first left header
        :param table_len: len of the table

        :return: selected_content, headers
        """

        try:
            # Not header on the left
            if len(header_left) == 0:
                rrt = RandomRelationalTable(self.evidence_per_table, self.column_per_table, self.rng)
                return rrt.relational_table(tbl,
                                            table_len,
                                            self.key_strategy
                                            )
            else:
                ret = RandomEntityTable(self.evidence_per_table, self.column_per_table, self.rng)
                return ret.entity_table(tbl,
                                        header_left,
                                        )
        except TableException:
            raise
