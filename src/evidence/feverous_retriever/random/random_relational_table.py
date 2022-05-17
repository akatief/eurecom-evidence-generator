import logging
from typing import List, Tuple
import numpy as np
import spacy
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable

from ..utils import TableException, TableExceptionType

# TODO: only relational_table is called. Find a better way to represent this class
class RandomRelationalTable:
    def __init__(self,
                 evidence_per_table,
                 columns_per_table,
                 rng: np.random.Generator,
                 ):
        self.rng = rng
        self.evidence_per_table = evidence_per_table
        self.columns_per_table = columns_per_table

    def relational_table(self,
                         table: WikiTable,
                         table_len: int,
                         key_strategy='random',
                         ) -> Tuple[List[List[Cell]], List[Cell]]:
        """
        Extract the evidence from the relational table.
        It returns the list of extracted evidences along with the headers.
        The length of each evidence is given by "column_per_table".

        :param table: The table to be scanned
        :param table_len: the length of the table
        :param rng: random numpy generator
        :param header: if you want to add the header or not
        :param key_strategy: heuristic for selecting the key column. Can be 'first', 'sensible' or None

        :return: the list of the selected cells and the content of the headers
        """
        # 0 for first table, 1 for second table, ...
        tbl_id = int(table.get_id().split('_')[1])

        try:
            index, start_row, end_row = self.sub_relational_table(table,
                                                                  table_len=table_len)
        except TableException:
            raise

        selected_header = table.get_header_rows()[index]

        # Now we have the range of correct rows associated to that specific header
        # from [start_i + 1,  end_i ]

        # randomly choose the evidence headers in the selected header
        if key_strategy == 'first':
            list_cols = [0] + self.rng.choice(len(selected_header.row),
                                              self.columns_per_table - 1,
                                              replace=False)
        elif key_strategy == 'sensible':
            # start_row + 1 is passed to skip the header
            list_cols = [RandomRelationalTable._key_sensible(table, selected_header.row, start_row + 1, end_row)] \
                        + self.rng.choice(len(selected_header.row),
                                          self.columns_per_table - 1,
                                          replace=False)
        elif key_strategy == 'entity':
            # start_row + 1 is passed to skip the header
            list_cols = [RandomRelationalTable._key_entity(table, selected_header.row, start_row + 1, end_row)] \
                        + self.rng.choice(len(selected_header.row),
                                          self.columns_per_table - 1,
                                          replace=False)
        elif key_strategy == 'random':
            # randomly choose the evidence headers in the selected header
            list_cols = self.rng.choice(len(selected_header.row),
                                        self.columns_per_table,
                                        replace=False)
        else:
            raise ValueError("Invalid choice of key detection strategy.")
        selected_h_cells = np.array(selected_header.row)[list_cols]

        # Now that we have the columns we randomly select #evidence_per_table rows
        possible_rows = np.arange(start_row + 1, end_row)

        # not enough rows to select
        if len(possible_rows) < self.evidence_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_ROW, table.page)

        list_rows = self.rng.choice(possible_rows,
                                    self.evidence_per_table,
                                    replace=False)

        selected_content = []
        for row in list_rows:
            try:
                selected_content.append([
                    table.get_cell(f'cell_{tbl_id}_{row}_{col}')
                    for col in list_cols
                ])
            except KeyError:
                raise TableException(TableExceptionType.ID_NOT_COMPLIANT, table.page)
        return selected_content, selected_h_cells

    def sub_relational_table(self,
                             tbl: WikiTable,
                             table_len: int,
                             ) -> Tuple[int, int, int]:
        """
        Given a table, it randomly finds a subtable which is used to sample the evidences

        :param tbl: tbl to which extract the subtable
        :param rng: random numpy generator
        :param table_len: length of the table

        :return: tuple containing
                (index of the header in [headers], header row_th, row_th subtable end)

        """

        # This is done due to the possibility of multiple
        # headers inside the table : table id => Thunder of the Gods'
        header_row_nums = [r.row_num
                           for r in tbl.get_header_rows()]  # [0, 1, 3, 4]

        selected_h = self.rng.choice(header_row_nums)  # 3

        # index in the list associated with value => 2
        selected_h_index = header_row_nums.index(selected_h)

        # This while is used to prevent selecting a subtable composed of zero rows
        # [H] Review scores | [H] Review scores
        # [H] Source | [H] Rating
        count = 0

        # define the last row of the subtable
        while True:

            # We select the last possible header
            if selected_h_index == len(header_row_nums) - 1:
                # the range of rows goes until the end of the table
                max_row_header = table_len

            else:
                # the range of rows ends before the last header
                max_row_header = header_row_nums[selected_h_index + 1]

            interval = max_row_header - selected_h
            # interval == 1 => consecutive headers
            # interval < num_evidence => not enough row to extract evidence
            if interval == 1 or interval < self.evidence_per_table:
                selected_h_index = (selected_h_index + 1) % len(header_row_nums)
                selected_h = header_row_nums[selected_h_index]
            else:
                break
            # to avoid infinite for loop
            # "Holy See–Philippines relations"
            if count == len(header_row_nums) * 2:
                raise TableException(TableExceptionType.SUBTABLE_NOT_FOUND, tbl.page)

            count += 1

        return selected_h_index, selected_h, max_row_header

    @staticmethod
    def _key_sensible(table, header, start_row, end_row):
        """
        Check table for all columns without duplicates and select one
        using heuristic based on data type and distance from left column

        :param table: The table to detect the key from
        :param header: The selected header of the subtable
        :param start_row: Row to begin analysis from
        :param end_row: Row to end analysis at
        """
        table_id = int(table.get_id().split('_')[1])
        n_cols = len(header)
        # Find candidate columns with all unique values and compute their scores
        candidates_scores = []
        for col in range(n_cols):
            values = []
            types = []
            for row in range(start_row, end_row):
                # Some tables have missing cells, skip them
                cell_id = f'cell_{table_id}_{row}_{col}'
                if cell_id in table.all_cells:
                    values.append(table.get_cell(cell_id))
                    if len(types) < 5:
                        types.append(RandomRelationalTable._get_type(table.get_cell(cell_id).content))
            if len(set(values)) == len(values): # If col contains no duplicates appends it to candidates
                col_type = RandomRelationalTable._col_type(types)
                candidates_scores.append(RandomRelationalTable._get_type_score(col, col_type))
        if len(candidates_scores) == 0: # If no columns are without duplicates defaults to first column
            return 0
        return np.argmax(candidates_scores)

    #TODO: refactor to avoid duplicating code
    @staticmethod
    def _key_entity(table, header, start_row, end_row):
        """
        Check table for all columns without duplicates and select one
        using heuristic based on named entity recognition and distance
        from left column

        :param table: The table to detect the key from
        :param header: The selected header of the subtable
        :param start_row: Row to begin analysis from
        :param end_row: Row to end analysis at
        """
        NER = spacy.load("en_core_web_sm")
        table_id = int(table.get_id().split('_')[1])
        n_cols = len(header)
        # Find candidate columns with all unique values and compute their scores
        candidates_scores = []
        for col in range(n_cols):
            values = []
            labels = []
            for row in range(start_row, end_row):
                # Some tables have missing cells, skip them
                cell_id = f'cell_{table_id}_{row}_{col}'
                if cell_id in table.all_cells:
                    values.append(table.get_cell(cell_id))
                    labels.append(NER(table.get_cell(cell_id).content))
            if len(set(values)) == len(values): # If col contains no duplicates appends it to candidates
                candidates_scores.append(RandomRelationalTable._get_entity_score(col, labels))
        if len(candidates_scores) == 0: # If no columns are without duplicates defaults to first column
            return 0
        return np.argmax(candidates_scores)


    @staticmethod
    def _get_type(n):
        if n.isdigit():
            return int
        else:
            try:
                float(n)
                return float
            except ValueError:
                return str

    @staticmethod
    def _col_type(types):
        col_type = int
        for t in types:
            if col_type is int and (t is float or t is str):
                col_type = t
            elif col_type is float and t is str:
                col_type = t
            else:
                break
        return col_type

    @staticmethod
    def _get_type_score(col, type):
        """
        Returns a score based on column position in table
        and type. The closer a column is to the left border
        the higher its score is. Strings score highest, followed
        by ints and floats.
        """
        if type is str:
            type_mult = 1
        elif type is int:
            type_mult = 0.5
        else: #float
            type_mult = 0.3
        return 1 / (col + 1) * type_mult

    @staticmethod
    def _get_entity_score(col, labels):
        """
        Returns a score based on column position in table
        and Entity. The closer a column is to the left border
        the higher its score is. A heuristics assigns a score
        to different types of entity
        """
        score = 0
        n_rows = len(labels)
        for l in labels:
            if l in ['EVENT', 'FAC', 'LAW', 'NORP', 'ORG', 'PERSON', 'PRODUCT', 'WORK_OF_ART']:
                # Score normalized by number of rows
                score += 1 / n_rows
            elif l in ['LANGUAGE', 'GPE', 'LOC']:
                score += 0.5 / n_rows
            elif l in ['CARDINAL', 'DATE', 'MONEY', 'ORDINAL', 'PERCENT', 'QUANTITY', 'TIME']:
                score += 0.3 / n_rows
        return 1 / (col + 1) * score
