from abc import ABC, abstractmethod
from typing import List, Tuple

import numpy as np
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage
from feverous.utils.wiki_page import WikiTable
from feverous.utils.wiki_table import Cell

from logger import logger
from ..evidence import Evidence
from ..evidence import EvidencePiece
from ..evidence_retriever import EvidenceRetriever

from .utils import TableException
from .utils import TableExceptionType
from .utils import check_header_left
from .utils import create_positive_evidence
from .utils import create_negative_evidence

from copy import deepcopy


class FeverousRetriever(EvidenceRetriever, ABC):
    """
    Retrieves evidence specifically from the FEVEROUS DB.
    """

    def __init__(self,
                 p_dataset: str,
                 num_positive: int,
                 num_negative: int,
                 wrong_cell: int,
                 table_per_page: int = 1,
                 evidence_per_table: int = 1,
                 column_per_table: int = 2,
                 seed: int = None,
                 verbose: bool = False):
        """

        :param p_dataset: path of the dataset
        :param num_positive: num of SUPPORTS evidence to generate
        :param num_negative: num of REFUTED evidence to generate
        :param wrong_cell: how many cells are swapped to create REFUTED evidences
        :param table_per_page: how many tables per page you want to scan
        :param evidence_per_table: how many Evidences from the same table
        :param column_per_table: how many cells for 1 Evidence
        :param seed: used for reproducibility
        :param verbose:if True, prints additional info during retrieval
        """
        super().__init__(n_pieces=num_positive, verbose=verbose)

        self.db = FeverousDB(p_dataset)  # Databes that contains the entire database
        self.path_db = p_dataset  # path used for extracting the dataset
        self.ids = list(self.db.get_non_empty_doc_ids())

        self.num_positive = num_positive
        self.num_negative = num_negative

        self.column_per_table = column_per_table
        self.wrong_cell = wrong_cell

        self.table_per_page = table_per_page
        self.evidence_per_table = evidence_per_table

        self.seed = seed
        # Random generator for reproducibility purposes
        self.rng = np.random.default_rng(self.seed)

    @property
    def retrieve(self
                 ) -> List[Evidence]:
        """
        Scans whole FEVEROUS dataset and returns list of Evidence objects.
        It extracts as many evidence as specified by num_evidence.

        Each Evidence is composed of number of columns.

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

        The algorithm is the following:
        1.0 shuffle the wikipedia pages
            1.1 filter out the wikipedia pages with num_table < table_per_page.
            1.2 filter out the tables with header_column < column_per_table
            1.3 filter out the subtables with num_row < evidence_per_table
        2.0 for page in ids:
            2.1 randomly select #table_per_page from the available tables
            2.2 extract the #num_evidence evidences

        :return: a list of Evidence objects composed of positive + negative
        """
        self.rng.shuffle(self.ids)  # shuffle the ids

        discarded_ids = dict()  # used to understand how many discarded pages
        discarded_ids[TableExceptionType.NO_ENOUGH_TBL.value] = []
        discarded_ids[TableExceptionType.NO_EXTRACTED_TBL.value] = []

        total_positive_evidences = []
        total_negative_evidences = []
        for page_name in self.ids:
            if self.verbose:
                logger.info(f" wikipage: {page_name}".encode("utf-8"))

            # retrieve the page
            page_json = self.db.get_doc_json(page_name)

            # parse the page in WikiPage format
            wiki_page = WikiPage(page_name, page_json)

            # Get all the tables
            tables = wiki_page.get_tables()

            if len(tables) < self.table_per_page:
                discarded_ids["NO_ENOUGH_TBL"] += [page_name]
                continue

            try:
                # analyze the tables of the wiki page
                pos_evidences, neg_evidences = self.analyze_tables(tables, wiki_page)
            except TableException as e:
                discarded_ids[e.error[0].value] += [e.error[1]]
            else:
                # compute only if no error
                if len(total_positive_evidences) < self.num_positive:
                    total_positive_evidences = total_positive_evidences + pos_evidences

                if len(total_negative_evidences) < self.num_negative:
                    total_negative_evidences = total_negative_evidences + neg_evidences

            if len(total_positive_evidences) >= self.num_positive and \
                    len(total_negative_evidences) >= self.num_negative:
                total_positive_evidences = total_positive_evidences[:self.num_positive]
                total_negative_evidences = total_negative_evidences[:self.num_negative]

                break

        if self.verbose:
            logger.info(
                f" Positive Evidences retrieved"
                f" {len(total_positive_evidences)}/{self.num_positive}"
            )
            logger.info(
                f" Negative Evidences retrieved"
                f" {len(total_negative_evidences)}/{self.num_negative}"
            )

            logger.info(f" Id not used {len(discarded_ids)}/{len(self.ids)}")

            logger.info(f' Id error NO_ENOUGH_TBL  {len(discarded_ids["NO_ENOUGH_TBL"])}')
            logger.info(f' Id error NO_EXTRACTED_TBL  '
                        f'{len(discarded_ids["NO_EXTRACTED_TBL"])}')

        return total_positive_evidences + total_negative_evidences

    def analyze_tables(self,
                       tables: List,
                       wiki_page: WikiPage,
                       ) -> Tuple[List[Evidence], List[Evidence]]:
        """
        it returns the evidence extracted from the tables inside the wikipage
        positive_evidences and negative_evidences.

        :param tables: the wiki page tables to analyze
        :param wiki_page: the current WikiPage object

        :return: the list of SUPPORT evidence and the list of REFUTED elements
        """
        # Shuffle the tables
        self.rng.shuffle(tables)

        positive_evidences = []
        negative_evidences = []
        count_extracted = 0  # how many table we have successfully extracted.

        for tbl in tables:  # for each table in wiki_page

            # Check how many evidences we have extracted from this wikipage
            if count_extracted >= self.table_per_page:
                break

            # get Table id
            tbl_id = int(tbl.get_id().split('_')[1])

            # get caption
            caption = [s for s in
                       wiki_page.get_context(f'table_caption_{tbl_id}')]
            # Add the caption to the table
            tbl.caption = caption

            # check if header on the left present
            header_left, table_len = check_header_left(tbl)

            # extract the evidence from the table
            try:
                evidence_from_table = self.get_evidence_from_table(tbl,
                                                                   header_left,
                                                                   table_len)
            except TableException:
                pass  # not raise because want to scan the other tables

            else:  # if no exception has occurred
                count_extracted += 1  # successfully extracted
                positive_evidences += create_positive_evidence(
                    deepcopy(evidence_from_table)
                )

                try:
                    negative_evidences += create_negative_evidence(
                        deepcopy(evidence_from_table),  # pass a copy
                        self.wrong_cell,
                        self.rng)
                except TableException:
                    # if not possible to create negative, continue with other tables
                    pass

        # Not enough evidence extracted from all the tables
        if count_extracted < self.table_per_page:
            raise TableException(
                TableExceptionType.NO_ENOUGH_TBL,
                wiki_page.title.get_id()
            )

        return positive_evidences, negative_evidences

    @abstractmethod
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
        pass  # abstract method
