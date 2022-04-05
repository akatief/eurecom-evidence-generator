from abc import ABC, abstractmethod
from typing import Tuple, List, Any

import hydra
from . import EvidenceRetriever
from . import Evidence
from . import EvidencePiece
from feverous.database.feverous_db import FeverousDB
from ..utils import WikiTable
from ..utils import WikiPage
import numpy as np


class FeverousRetriever(EvidenceRetriever, ABC):
    """
    Retrieves evidence specifically from the FEVEROUS DB.
    """

    def __init__(self,
                 p_dataset: str,
                 num_evidence: int,
                 n_pieces: int,
                 table_per_page=1,
                 evidence_per_table=1,
                 column_per_table=2,
                 seed=None,
                 verbose=False):
        """
        :param p_dataset: path of the dataset
        :param num_evidence: how many Evidences you want to get
        :param n_pieces: ?
        :param table_per_page: how many tables per page you want to scan
        :param evidence_per_table: how many Evidences from the same table
        :param column_per_table: how many cells for 1 Evidence
        :param seed: used for reproducibility
        :param verbose: if True, prints additional info during retrieval
        """
        super().__init__(n_pieces=num_evidence)

        self.db = FeverousDB(p_dataset)  # Databes that contains the entire database
        self.path_db = p_dataset  # path used for extracting the dataset
        self.ids = list(self.db.get_non_empty_doc_ids())  # to be changed

        self.p_dataset = p_dataset
        self.num_evidence = num_evidence
        self.table_per_page = table_per_page
        self.evidence_per_table = evidence_per_table
        self.column_per_table = column_per_table
        self.seed = seed
        self.verbose = verbose

    def retrieve(
            self
    ) -> list[Evidence]:
        """
        Scans whole FEVEROUS dataset and returns list of Evidence objects.
        It extracts a number of evidence specified by num_evidence.

        Each Evidence is composed of number of columns. columns Evidence Pieces

        Example:
            [
                Evidence(
                    EvidencePiece('Totti', 'name'),
                    EvidencePiece(128, 'scored_gol)
                    "SUPPORTS"
                ),
                Evidence(
                    EvidencePiece('Cassano', 'name'),
                    EvidencePiece(128, 'scored_gol)
                    "REFUTED"
                ),
                ...
            ]


        1.0 shuffle the wikipedia pages
            1.1 filter out the wikipedia pages with num_table < table_per_page.
            1.2 filter out the tables with header_column < column_per_table
            1.3 filter out the subtables with num_row < evidence_per_table
        2.0 for page in ids:
            2.1 randomly select #table_per_page from the available tables
            2.2 extract the #num_evidence evidences

        :return: a list of Evidence objects
        """
        # Random generator for reproducibility purposes
        rng = np.random.default_rng(self.seed)
        rng.shuffle(self.ids)

        # TODO: to shuffle or not to shuffle the ids?
        discarded_ids = []
        total_evidences = []
        for id in self.ids[:]:
            # retrieve the page
            page_json = self.db.get_doc_json(id)
            if self.verbose: print('%%%%%%%%%%%%%%%%%%%%%% new_id ', id)

            # parse the page in WikiPage format
            wiki_page = WikiPage(id, page_json)

            # Get all the tables
            tables = wiki_page.get_tables()

            if len(tables) < self.table_per_page:
                continue

            # Shuffle the tables
            rng.shuffle(tables)

            # for each table in wiki_page
            for i, tbl in enumerate(tables):
                # print(tbl)
                # get the left indexes
                if i >= self.table_per_page:
                    break

                # TODO possible bug: check what happen with multiple row
                header_left, table_len = self.get_index(tbl)
                evidence_from_table = self.get_evidence_from_table(tbl,
                                                                   header_left,
                                                                   table_len,
                                                                   rng=rng)

                if evidence_from_table is not None:
                    for e in self.create_positive_evidence(evidence_from_table):
                        total_evidences.append(e)

                else:
                    discarded_ids.append(id)

            if len(total_evidences) == self.num_evidence:
                break
            if len(total_evidences) > self.num_evidence:
                total_evidences = total_evidences[:self.num_evidence]
        if self.verbose:
            print(f"Evidences retrieved {len(total_evidences)}/{self.num_evidence}")
            print(f"Id not used {len(discarded_ids)}/{len(self.ids)}")

        return total_evidences

    def create_positive_evidence(self,
                                 evidence_from_table: list[list[EvidencePiece]],
                                 ) -> list[Evidence]:
        """
        It takes as argument the List of EvidencePieces created from a specific table.
        It returns the list of Evidence object created from each set of EvidencePieces.

        :param evidence_from_table: each element is [EvidencePiece] got from the table

        :return positive_evidences: list containing the positive Evidence
        """
        positive_evidences = []
        for evidence_piece in evidence_from_table:
            positive_evidences.append(
                Evidence(
                    evidence_piece,
                    self.column_per_table,
                    "SUPPORTS",
                    self.seed
                )
            )

        return positive_evidences

    def create_negative_evidence(self):
        # TODO: implement_negative_evidence
        pass

    def get_index(self,
                  tbl: WikiTable
                  ) -> tuple[list[tuple[Any, Any, Any]], int]:
        """
        it scans all the table to check if header on the left are present

        :param tbl: table to be scanned WikiTable

        :return header_index: list of tuple (header_cell_id, row_number,content)
        :return count: number of rows in the table
        """
        header_index = []
        count = 0
        for row in tbl.get_rows():
            count += 1
            if row.is_header_row():
                continue

            else:
                # TODO: now I am checking only the first column,
                #       possible headers in the center?
                first_cell = row.get_row_cells()[0]
                if first_cell.is_header:
                    # (header_cell_id, row_number)
                    header_index.append(
                        (first_cell.name, int(row.row_num), first_cell.content))

        return header_index, count

    @abstractmethod
    def get_evidence_from_table(self,
                                tbl: WikiTable,
                                header_left: list[tuple[str, int, str]],
                                table_len: int,
                                if_header=True,
                                rng=None) -> list[list[EvidencePiece]]:
        """
        it is used to extract the "meaningful" attributes from one table at time.
        "Meaningful" is defined by the target application.

        Example:
        evidences =
            [
                [
                    EvidencePiece('Totti', 'name'),
                    EvidencePiece(128, 'scored_gol)
                ],
                [
                    ...
                ],
                ...
            ]

        :param tbl: scanned table WikiTable
        :param header_left: list of tuple. Each element contains the first left header
        :param table_len: number of row in the table, scalar
        :param if_header: add or not add the header in the output Boolean
        :param rng: Random numpy generator
        """
        pass
