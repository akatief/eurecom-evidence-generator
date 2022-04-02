from abc import ABC, abstractmethod
from typing import Tuple, List, Any

import hydra

from utils import WikiTable
from evidence_retriever import EvidenceRetriever
from evidence import Evidence, EvidencePiece

from database import FeverousDB
from utils import WikiPage
import numpy as np


class FEVEROUSRetriever(EvidenceRetriever, ABC):
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
                 seed=None):
        """
        :param p_dataset: path of the dataset
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

    def retrieve(self,
                 data):
        """
        Scans whole FEVEROUS dataset and returns list of Evidence objects.
        It extracts a number of evidence specified by num_evidence.

        1.0 shuffle the wikipedia pages
            1.1 filter out the wikipedia pages with num_table < table_per_page.
            1.2 filter out the tables with header_column < column_per_table
            1.3 filter out the subtables with num_row < evidence_per_table
        2.0 for page in ids:
            2.1 randomly select #table_per_page from the available tables
            2.2 extract the #num_evidence evidences

        :param data: data to retrieve evidence from

        :return: a list of Evidence objects
        """
        # Random generator for reproducibility purposes
        rng = np.random.default_rng(self.seed)
        rng.shuffle(self.ids)

        # TODO: to shuffle or not to shuffle?
        discarded_ids = []
        tbl_evidences = []
        for id in self.ids[:]:
            # retrieve the page
            page_json = self.db.get_doc_json(id)
            print('%%%%%%%%%%%%%%%%%%%%%% new_id ', id)

            # parse the page in WikiPage format
            wiki_page = WikiPage(id, page_json)

            # Get all the tables
            tables = wiki_page.get_tables()

            if len(tables) < self.table_per_page:
                continue

            # Shuffle the tables
            rng.shuffle(tables)

            # for each table in wiki_page
            for tbl in tables:
                # print(tbl)
                # get the left indexes

                # TODO possible bug: check what happen with multiple row
                header_left, table_len = self.get_index(tbl)
                output = self.get_evidence(tbl,
                                           header_left,
                                           table_len,
                                           self.column_per_table,
                                           self.evidence_per_table,
                                           rng=rng)

                if output is not None:
                    tbl_evidences.append(Evidence(output,
                                                  len(output),
                                                  self.table_per_page,
                                                  self.evidence_per_table,
                                                  self.column_per_table,
                                                  self.seed))
                else:
                    discarded_ids.append(id)

            if len(tbl_evidences) >= self.num_evidence:
                break

        # TODO bug: more evidence than necessary
        print(f"Evidences retrieved {len(tbl_evidences)}/{self.num_evidence}")
        print(f"Id not usede {len(discarded_ids)}/{len(self.ids)}")

        return tbl_evidences

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
                        (first_cell.name, row.row_num, first_cell.content))

        return header_index, count

    @abstractmethod
    def get_evidence(self,
                     tbl: WikiTable,
                     header_left,
                     table_len: int,
                     if_header=True,
                     rng=None) -> list[EvidencePiece]:
        pass






