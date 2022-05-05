import logging
from typing import List, Tuple
import numpy as np
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
                         key_strategy = None,
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
            list_cols = [self._key_sensible(table, selected_header.row, start_row + 1, end_row)] \
                        + self.rng.choice(len(selected_header.row),
                                          self.columns_per_table - 1,
                                          replace=False)
        else:
            # randomly choose the evidence headers in the selected header
            list_cols = self.rng.choice(len(selected_header.row),
                                        self.columns_per_table,
                                        replace=False)

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

    # TODO: implement more sensible heuristics
    #       Look for entities, look for textual headers. String > int > ...
    #       Make a ranking based on closeness to left and type
    #       Strings are better than numericals, see Prof. resources
    def _key_sensible(self,table, header, start_row, end_row):
        """
        Check table for all columns without duplicates and select one
        based on some heuristic

        :param table: The table to detect the key from
        :param header: The selected header of the subtable
        :param start_row: Row to begin analysis from
        :param end_row: Row to end analysis at
        """
        table_id = int(table.get_id().split('_')[1])
        n_cols = len(header)
        candidates = []
        for col in range(n_cols):
            values = []
            for row in range(start_row, end_row):
                # Some tables have missing cells, skip them
                cell_id = f'cell_{table_id}_{row}_{col}'
                if cell_id in table.all_cells:
                    values.append(table.get_cell(cell_id))
            if len(set(values)) == len(values): # If col contains no duplicates appends it to candidates
                candidates.append(col)
        if len(candidates) == 0: # If no columns are without duplicates defaults to first column
            return 0
        else: # Else returns first potential primary key found
            return candidates[0]

