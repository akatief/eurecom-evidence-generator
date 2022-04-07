from typing import List, Tuple

import numpy as np
from numpy import ndarray
from feverous.utils.wiki_table import Cell

from evidence import EvidencePiece
from . import FeverousRetriever
from feverous.utils.wiki_page import WikiTable


class FeverousRandomRetriever(FeverousRetriever):
    def get_evidence_from_table(self,
                                tbl: WikiTable,
                                header_left: List[Tuple[str, int, str]],
                                table_len: int,
                                if_header=True,
                                rng=None) -> ndarray:
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
          :param if_header: add or not add the header in the output Boolean
          :param rng: random numpy generator

          :return evidences: contains the list of evidences from this table
        """
        # 0 for first table, 1 for second table, ...
        tbl_id = int(tbl.get_id().split('_')[1])

        # returns multiple Row that are headers
        headers = tbl.get_header_rows()

        # No row headers in the table
        # table id = Allerheiligenstriezel
        if len(headers) == 0 and len(header_left) == 0:
            return None

        # TODO bug: Pivot table not header row 'Miguel Ángel Rodríguez (squash player)'
        # Not enough column for one Evidence
        # TODO: headers row may have different legth
        if len(headers) != 0 and len(headers[0].row) < self.column_per_table:
            return None

        output = self.random_strategy(tbl_id,
                                      tbl,
                                      header_left,
                                      table_len,
                                      if_header,
                                      rng)

        if output is None:
            return None

        selected_cells, selected_h_cells = output
        evidences = []
        for evidence in selected_cells:
            local_evidences = []
            for i, c in enumerate(evidence):
                local_evidences.append(EvidencePiece(tbl.page,
                                                     tbl.caption,
                                                     c,
                                                     selected_h_cells[i]))

            evidences.append(np.array(local_evidences))

        return np.array(evidences)

    def random_strategy(self,
                        tbl_id: int,
                        tbl: WikiTable,
                        header_left: List[Tuple[str, int, str]],
                        table_len: int,
                        if_header: bool,
                        rng: np.random.Generator
                        ) -> Tuple[List[List[Cell]], List[str]]:
        """
        It returns the list of evidences extracted from the table.
        the length of the list depends on "evidence_per_table"
        Example:
            selected_content = [['Totti', 128], ['Cassano', 103], ...]
            headers = ['name', 'scored_gol']

        :param tbl_id: index associated with the table in the page
        :param tbl: one table present in the page
        :param header_left: list of tuple. Each element contains the first left header
        :param table_len: len of the table
        :param if_header: to insert or not the header
        :param rng: random generator for reproducibility

        :return: selected_content, headers
        """

        # TODO implement: Implement pivot table
        # Not header on the left
        if len(header_left) == 0:
            return self.relational_table(tbl,
                                         tbl_id,
                                         table_len,
                                         rng,
                                         if_header
                                         )
        else:
            # TODO: implement pivot table
            return self.entity_table(tbl,
                                     tbl_id,
                                     header_left,
                                     rng,
                                     if_header
                                     )

    def relational_table(self,
                         tbl: WikiTable,
                         tbl_id: int,
                         table_len: int,
                         rng: np.random.Generator,
                         if_header: bool,
                         ) -> Tuple[List[List[Cell]], List[str]]:
        """
        Extract the evidence from the relational table.
        It returns the list of extracted evidences along with the headers.
        The length of each evidence is given by "column_per_table".

        :param tbl: The table to be scanned
        :param tbl_id: the table number in the page. 0 for first table, 1, ...
        :param table_len: the length of the table
        :param rng: random numpy generator
        :param if_header: if you want to add the header or not

        :return: the list of the selected cells and the content of the headers
        """

        output = self.sub_relational_table(tbl,
                                           rng=rng,
                                           table_len=table_len)
        if output is None:
            return None

        index, start_i, end_i = output

        # Row class associated with the index
        selected_header = tbl.get_header_rows()[index]

        # Now we have the range of correct rows associated to that specific header
        # from [start_i + 1,  end_i ]

        # randomly choose the headers
        list_j = rng.choice(len(selected_header.row),
                            self.column_per_table,
                            replace=False)
        selected_h_cells = np.array(selected_header.row)[list_j]
        selected_h_cells = [h.content for h in selected_h_cells]

        # Now that we have the columns we randomly select #evidence_per_table rows
        possible_rows = np.arange(start_i + 1, end_i)

        # not enough rows to select
        if len(possible_rows) < self.evidence_per_table:
            return None

        list_i = rng.choice(possible_rows, self.evidence_per_table, replace=False)

        # TODO bug: understand if assumption on id is correct
        # try:  # we discard the table with different ids
        #     for i in list_i:
        #         selected_content = [tbl.get_cell(f'cell_{tbl_id}_{i}_{j}')
        #                             for j in list_j]
        # except:
        #     print('error in retrieving the cell')
        #     return None
        selected_content = []
        for i in list_i:
            try:
                selected_content.append([tbl.get_cell(f'cell_{tbl_id}_{i}_{j}')
                                         for j in list_j])
            except Exception:
                return None

        if if_header:
            return selected_content, selected_h_cells
        else:
            return selected_content, None

    def sub_relational_table(self,
                             tbl: WikiTable,
                             rng: np.random.Generator,
                             table_len: int,
                             ) -> Tuple[int, int, int]:
        """
        Given a table, it randomly finds a subtable which is used to sample the evidences

        :param tbl: tbl to which extract the subtable
        :param rng: random numpy generator
        :param table_len: lenght of the table

        :return: tuple containing
                (index of the header in [headers], header row_th, row_th subtable end)

        """

        # This is done due to the possibility of multiple
        # headers inside the table : table id => Thunder of the Gods'
        header_row_nums = [r.row_num for r in
                           tbl.get_header_rows()]  # [0, 1, 3, 4]
        i_header = rng.choice(header_row_nums)  # 3
        # index in the list associated with value => 2
        random_row_h_index = header_row_nums.index(i_header)

        # This while is used to prevent selecting a subtable composed of zero rows
        # [H] Review scores | [H] Review scores
        # [H] Source | [H] Rating
        count = 0
        while True:
            # define the last row of the subtable
            # We select the last possible header
            if random_row_h_index == len(header_row_nums) - 1:
                # the range of rows goes until the end of the table
                max_row_header = table_len
            else:
                # the range of rows ends before the last header
                max_row_header = header_row_nums[random_row_h_index + 1]

            len_interval = max_row_header - i_header
            # len_interval == 1 => consecutive headers
            # len_interval < num_evidence => not enough row to extract evidence
            if len_interval == 1 or len_interval < self.evidence_per_table:
                random_row_h_index = (random_row_h_index + 1) % len(header_row_nums)
                i_header = header_row_nums[random_row_h_index]
            else:
                break
            # to avoid infinite for loop
            # "Holy See–Philippines relations"
            if count == len(header_row_nums) * 2:
                return None

            count += 1

        return random_row_h_index, i_header, max_row_header

    def entity_table(self,
                     tbl: WikiTable,
                     tbl_id: int,
                     header_left: List[Tuple[str, int, str]],
                     rng: np.random.Generator,
                     if_header: bool,
                     ) -> Tuple[List[List[Cell]], List[str]]:
        """
        Extract the Evidences from the entity table i.e. from the header left

        :param tbl: one table present in the page
        :param tbl_id: index associated with the table in the page
        :param header_left: list of tuple. Each element contains the first left header
        :param rng: random generator
        :param if_header: to insert or not the header

        :return: the list of the selected cells and the content of the headers
        """
        # header_left [(header_cell_id, row_number,content), ... ]
        header_left = np.array(header_left)

        # Not enough rows
        if len(header_left) < self.column_per_table:
            return None

        selected_headers = rng.choice(header_left,
                                      self.column_per_table,
                                      replace=False)

        # Now we need to select the cells from the selected headers
        rows = np.array(tbl.get_rows())
        i = selected_headers[:, 1].astype(int)

        selected_rows = rows[i]  # take only the selected row

        extracted_cell = []
        for r in selected_rows:
            # Not enough cells

            unique_cells = [r.row[0]]
            for c in r.row[1:]:
                if c.content in [u.content for u in unique_cells]:
                    continue
                unique_cells.append(c)

            if len(unique_cells) - 1 < self.evidence_per_table:
                return None

            cells = rng.choice(unique_cells[1:],
                               self.evidence_per_table,
                               replace=False)

            extracted_cell.append(cells)

        selected_content = np.transpose(extracted_cell)
        headers = selected_headers[:, 2]
        return selected_content, headers
