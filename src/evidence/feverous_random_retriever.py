from typing import Any, Optional, Tuple, List
from xmlrpc.client import boolean

import hydra
import numpy as np
from numpy import ndarray

from database import FeverousDB
from evidence import EvidencePiece
from feverous_retriever import FEVEROUSRetriever
from utils import WikiPage, WikiTable
from utils.wiki_table import Cell


class FeverousRandomRetriever(FEVEROUSRetriever):

    def __init__(self,
                 p_dataset,
                 num_evidence,
                 n_pieces,
                 table_per_page=1,
                 evidence_per_table=1,
                 column_per_table=2,
                 seed=None):
        super().__init__(
            p_dataset,
            num_evidence,
            n_pieces,
            table_per_page,
            evidence_per_table,
            column_per_table,
            seed)

    def retrieve(self, data):
        return super().retrieve(data)

    def get_evidence(self,
                     tbl: WikiTable,
                     header_left: list[tuple[str, int, str]],
                     table_len: int,
                     if_header=True,
                     rng=None) -> List[EvidencePiece]:
        """
          it is used to extract the "meaningful" attributes from one table at time.
          "Meaningful" is defined by the target application.

          :param tbl: scanned table WikiTable
          :param header_left: list of tuple. Each element contains the first left header
          :param table_len: number of row in the table, scalar
          :param if_header: add or not add the header in the output Boolean
          :param rng: Random numpy generator
        """
        tbl_id = int(tbl.get_id()[-1])  # 0 for first table, 1 for second table, ...
        headers = tbl.get_header_rows()  # returns multiple Row that are headers!

        # TODO bug: Pivot table not header row  'Miguel Ángel Rodríguez (squash player)'
        # Not enough column
        if len(headers[0].row) < self.column_per_table:
            return None

        output = self.random_strategy(tbl_id,
                                      tbl,
                                      header_left,
                                      table_len,
                                      if_header,
                                      rng)

        # TODO: Implement not correct tables
        if output is None:
            return None

        selected_cells, selected_h_cells = output
        evidences = []
        for evidence in selected_cells:
            for i, c in enumerate(evidence):
                evidences.append(EvidencePiece(tbl.page, c, selected_cells[i]))

        return np.array(evidences)

    def random_strategy(self,
                        tbl_id: int,
                        tbl: WikiTable,
                        header_left: list[tuple[str, int, str]],
                        table_len: int,
                        if_header: boolean,
                        rng: np.random.Generator
                        ) -> tuple[list[list[Cell]], list[str]]:

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
            raise RuntimeError('Not yet implemented')

    def find_sub_table(self,
                       tbl: WikiTable,
                       rng: np.random.Generator,
                       table_len: int,
                       ) -> tuple[int, int, int]:
        """
        Given a table, it randomly finds a subtable which is used to sample the evidences

        :param tbl: tbl to wich extract the subtable
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
            if len_interval == 1 or len_interval < self.num_evidence:
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

    def relational_table(self,
                         tbl: WikiTable,
                         tbl_id: int,
                         table_len: int,
                         rng: np.random.Generator,
                         if_header: boolean,
                         ) -> tuple[list[list[Cell]], list[str]]:
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

        output = self.find_sub_table(tbl,
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
        list_j = rng.choice(len(selected_header.row), self.column_per_table,
                            replace=False)
        selected_h_cells = np.array(selected_header.row)[list_j]

        # Now that we have the columns we randomly select #num_evidence rows
        possible_rows = np.arange(start_i + 1, end_i)

        if len(possible_rows) < self.num_evidence:
            return None

        list_i = rng.choice(possible_rows, self.num_evidence, replace=False)

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
            selected_content.append([tbl.get_cell(f'cell_{tbl_id}_{i}_{j}')
                                     for j in list_j])

        if if_header:
            return selected_content, selected_h_cells
        else:
            return selected_content, None


@hydra.main(config_path="../config/", config_name="config.yaml")
def main(cfg):
    print(type(cfg))
    db = FeverousDB(cfg.data_path)
    page_id = 'List of Flash animated films'
    page_json = db.get_doc_json(page_id)
    wiki_page = WikiPage(page_id, page_json)

    wiki_tables = wiki_page.get_tables()  # return list of all Wiki Tables
    # print(wiki_tables[0].all_cells)
    # print(wiki_tables[0])

    class_feverous = FeverousRandomRetriever(cfg.data_path,
                                             cfg.num_evidence,
                                             cfg.n_pieces,
                                             cfg.table_per_page,
                                             cfg.evidence_per_table,
                                             cfg.column_per_table,
                                             cfg.seed
                                             )

    rng = np.random.default_rng(cfg.seed)
    evidences = class_feverous.get_evidence(wiki_tables[0],
                                [],
                                70,
                                rng=rng)

    print(evidences.shape)


    # selected_content, selected_h_cells = class_feverous.relational_table(wiki_tables[0],
    #                                                                      0,
    #                                                                      25,
    #                                                                      rng,
    #                                                                      True
    #                                                                      )
    # print(selected_content[0], '\n')
    # print(selected_h_cells[0], '\n')


if __name__ == '__main__':
    main()
