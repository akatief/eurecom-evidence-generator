from abc import ABC, abstractmethod
from typing import List, Tuple

import numpy as np
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage
from feverous.utils.wiki_page import WikiTable
from feverous.utils.wiki_table import Cell

from evidence import Evidence
from evidence import EvidencePiece
from evidence import EvidenceRetriever

from logger import logger
from .utils import TableException, TableExceptionType, check_header_left, \
    create_positive_evidence


class FeverousRetriever(EvidenceRetriever, ABC):
    """
    Retrieves evidence specifically from the FEVEROUS DB.
    """

    def __init__(self,
                 p_dataset: str,
                 num_evidence: int,
                 table_per_page=1,
                 evidence_per_table=1,
                 column_per_table=2,
                 seed=None,
                 verbose=True):
        """
        :param p_dataset: path of the dataset
        :param num_evidence: how many Evidences you want to get
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
    ) -> List[Evidence]:
        """
        Scans whole FEVEROUS dataset and returns list of Evidence objects.
        It extracts as evidence as specified by num_evidence.

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

        :return: a list of Evidence objects
        """
        # Random generator for reproducibility purposes
        rng = np.random.default_rng(self.seed)
        rng.shuffle(self.ids)

        discarded_ids = dict()
        discarded_ids[TableExceptionType.NO_HEADERS.value] = []
        discarded_ids[TableExceptionType.NO_ENOUGH_ROW.value] = []
        discarded_ids[TableExceptionType.SUBTABLE_NOT_FOUND.value] = []
        discarded_ids[TableExceptionType.ID_NOT_COMPLIANT.value] = []
        discarded_ids[TableExceptionType.NO_ENOUGH_COL.value] = []
        discarded_ids[TableExceptionType.NO_ENOUGH_TBL.value] = []

        total_evidences = []
        for page_name in self.ids[:]:
            if self.verbose:
                logger.info(f" wikipage: {page_name}".encode("utf-8"))

            # retrieve the page
            page_json = self.db.get_doc_json(page_name)

            # parse the page in WikiPage format
            wiki_page = WikiPage(page_name, page_json)

            # Get all the tables
            tables = wiki_page.get_tables()

            # Todo: add it to the list
            if len(tables) < self.table_per_page:
                discarded_ids["NO_ENOUGH_TBL"] += [page_name]
                continue

            # Shuffle the tables
            rng.shuffle(tables)

            try:
                evidences = self.analize_tables(rng, tables, wiki_page)
                total_evidences = total_evidences + evidences
            except TableException as e:
                discarded_ids[e.error[0].value] += [e.error[1]]

            if len(total_evidences) >= self.num_evidence:
                total_evidences = total_evidences[:self.num_evidence]
                break

        if self.verbose:
            logger.info(f" Evidences retrieved {len(total_evidences)}/{self.num_evidence}")
            logger.info(f" Id not used {len(discarded_ids)}/{len(self.ids)}")
            logger.info(f' Id error NO_HEADERS  {len(discarded_ids["NO_HEADERS"])}')
            logger.info(f' Id error NO_ENOUGH_ROW  {len(discarded_ids["NO_ENOUGH_ROW"])}')
            logger.info(f' Id error NO_ENOUGH_COL  {len(discarded_ids["NO_ENOUGH_ROW"])}')
            logger.info(f' Id error SUBTABLE_NOT_FOUND '
                        f'{len(discarded_ids["SUBTABLE_NOT_FOUND"])}')
            logger.info(f' Id error ID_NOT_COMPLIANT '
                        f'{len(discarded_ids["ID_NOT_COMPLIANT"])}')

        return total_evidences

    def analize_tables(self,
                       rng: np.random.Generator,
                       tables: List,
                       wiki_page: WikiPage,
                       ) -> List:

        # for each table in wiki_page
        for i, tbl in enumerate(tables):

            # Check if already scanned enough table from wikipage
            if i >= self.table_per_page:
                break

            # get Table id
            tbl_id = int(tbl.get_id().split('_')[1])

            # get caption
            caption = [str(s) for s in
                       wiki_page.get_context(f'table_caption_{tbl_id}')]

            # Add the caption to the table
            tbl.caption = caption

            # check if header on the left present
            header_left, table_len = check_header_left(tbl)

            # extract the evidence from the table
            try:
                evidence_from_table = self.get_evidence_from_table(tbl,
                                                                   header_left,
                                                                   table_len,
                                                                   rng=rng)
            except TableException:
                raise

            else:
                positive_evidences = create_positive_evidence(evidence_from_table,
                                                              self.column_per_table,
                                                              self.seed)

                return positive_evidences

    @abstractmethod
    def get_evidence_from_table(self,
                                tbl: WikiTable,
                                header_left: List[Tuple[Cell, int, str]],
                                table_len: int,
                                if_header=True,
                                rng=None) -> List[List[EvidencePiece]]:
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
