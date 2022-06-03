from typing import List, Tuple
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable
from ....logger import logger

from ...evidence import EvidencePiece
from ..feverous_retriever import FeverousRetriever
from .random_entity_table import entity_table
from .random_relational_table import relational_table
from ..utils import TableExceptionType, TableException


class FeverousRetrieverRandom(FeverousRetriever):
    # TODO: make init with kwargs
    def __init__(self,
                 p_dataset: str,
                 num_positive: int,
                 num_negative: int,
                 wrong_cell: int,
                 table_per_page=1,
                 evidence_per_table=1,
                 column_per_table=2,
                 key_strategy=None,
                 seed=None,
                 verbose=False):
        super().__init__(p_dataset, num_positive, num_negative, wrong_cell,
                         table_per_page, evidence_per_table, column_per_table, seed,
                         verbose)
        self.key_strategy = key_strategy

    def get_evidence_from_table(self,
                                tbl: WikiTable,
                                header_left: List[Cell],
                                table_len: int
                                ) -> List[List[EvidencePiece]]:
        """
        extract the EvidencePieces from one table. This functions does not directly
        compute the Evidence because possible evidence with EvidencePieces coming from
        different tables.

        :param tbl: WikiTable to scan
        :param header_left: list of left header cells
        :param table_len: number of rows in the table, scalar

        :return: a list of lists of EvidencePiece objects
        """
        # returns multiple Row that are headers
        headers = tbl.get_header_rows()

        # no headers at all in the table
        if len(headers) == 0 and len(header_left) == 0:
            raise TableException(TableExceptionType.NO_HEADERS, tbl.page)

        # not enough columns in the Relational table
        if len(headers) != 0 and len(headers[0].row) <= self.column_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)
        # not enough columns in the entity table
        if len(header_left) != 0 and len(header_left) <= self.column_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)

        try:
            # extract the evidencePieces with the random strategy
            output = self.random_strategy(tbl,
                                          header_left,
                                          table_len)
        except TableException:
            raise  # propagate up the TableException

        selected_cells, selected_h_cells, possible_pieces = output

        evidences = []
        for evidence in selected_cells:
            local_evidences = []
            for i, cell in enumerate(evidence):
                local_evidences.append(
                    EvidencePiece(tbl.page,
                                  tbl.caption,
                                  cell,
                                  selected_h_cells[i],
                                  possible_pieces[i]
                                  )
                )
            evidences.append(local_evidences)

        return evidences

    def random_strategy(self,
                        tbl: WikiTable,
                        header_left: List[Cell],
                        table_len: int,
                        ) -> Tuple[
        List[List[Cell]],
        List[Cell],
        List[List[Cell]]
    ]:
        """
        The strategy is different depending on the type of table is analyzed.
        The different strategies are implemented in the utils of the random package.
        Example:
            selected_content = [['Totti', 128], ['Cassano', 103], ...]
            headers = ['name', 'scored_gol']
            possible_pieces = [ ['Totti', 'Cassano'], [128, 103]]

        :param tbl: the analyzed table
        :param header_left: list of header left cells
        :param table_len: len of the table

        :return selected_cells: [ ['Totti', 128], ['Cassano', 103], ...]
        :return selected_h_cells: ['name', 'scored_gol']
        :return possible_pieces: the swappable cells for each header
        """

        try:
            # Not header on the left
            if len(header_left) == 0:
                selected_evidences, selected_h_cells, alternative_pieces = relational_table(tbl,
                                                                                            table_len,
                                                                                            self.rng,
                                                                                            self.evidence_per_table,
                                                                                            self.column_per_table,
                                                                                            self.key_strategy
                                                                                            )
                if self.verbose:
                    logger.info(f"Page: {tbl.page} {tbl.get_id()} Selected headers: {[str(cell) for cell in selected_h_cells]}".encode("utf-8"))
                return selected_evidences, selected_h_cells, alternative_pieces
            else:
                return entity_table(tbl,
                                    header_left,
                                    self.rng,
                                    self.column_per_table,
                                    self.evidence_per_table
                                    )
        except TableException:
            raise
