from typing import List, Tuple
import numpy as np
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable

from ..utils import TableException, TableExceptionType


def relational_table(
        tbl: WikiTable,
        table_len: int,
        rng: np.random.Generator,
        evidence_per_table: int,
        column_per_table: int
) -> Tuple[
    List[List[Cell]],
    List[Cell],
    List[List[Cell]]
]:
    """
    Extract the evidence from the relational table.
    It returns the list of extracted evidences along with the headers.
    The length of each evidence is given by "column_per_table".
    The retuned list, is a list of list:
        evidence_1: [EvidencePiece1, EvidencePiece2],
        evidence_2: [EvidencePiece1, EvidencePiece2],

    :param column_per_table:
    :type column_per_table:
    :param evidence_per_table:

    :param tbl: The table to be scanned
    :param table_len: the length of the table
    :param rng: random numpy generator
    :return: the list of the selected cells and the content of the headers
    """
    # 0 for first table, 1 for second table, ...
    tbl_id = int(tbl.get_id().split('_')[1])
    ept = evidence_per_table
    try:
        index, start_i, end_i = sub_relational_table(tbl, rng=rng,
                                                     table_len=table_len,
                                                     evidence_per_table=ept)
    except TableException:
        raise

    tbl_headers = tbl.get_header_rows()[index]

    # Now we have the range of correct rows associated to that specific header
    # from [start_i + 1,  end_i ]

    # randomly choose the evidence headers in the selected header
    list_j = rng.choice(len(tbl_headers.row),
                        column_per_table,
                        replace=False)

    selected_h_cells = np.array(tbl_headers.row)[list_j]

    # Now that we have the columns we randomly select #evidence_per_table rows
    possible_rows = np.arange(start_i + 1, end_i)

    # not enough rows to select
    if len(possible_rows) < evidence_per_table:
        raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

    try:
        possible_pieces = extract_possible_pieces(list_j, possible_rows, tbl, tbl_id)
    except KeyError:
        raise TableException(TableExceptionType.ID_NOT_COMPLIANT, tbl.page)

    list_i = rng.choice(possible_rows,
                        evidence_per_table,
                        replace=False)

    selected_evidences = []
    for i in list_i:  # For each row

        evidence = []
        for j in list_j:  # For each column
            try:
                evidence += [tbl.get_cell(f'cell_{tbl_id}_{i}_{j}')]
            except KeyError:
                raise TableException(TableExceptionType.ID_NOT_COMPLIANT, tbl.page)

        selected_evidences.append(evidence)

    return selected_evidences, selected_h_cells, possible_pieces


def extract_possible_pieces(list_j, possible_rows, tbl, tbl_id):
    possible_pieces = []
    for j in list_j:

        column_evidence_pieces = []
        for i in possible_rows:
            column_evidence_pieces += [tbl.get_cell(f'cell_{tbl_id}_{i}_{j}')]

        possible_pieces.append(column_evidence_pieces)
    return possible_pieces


def sub_relational_table(
        tbl: WikiTable,
        rng: np.random.Generator,
        table_len: int,
        evidence_per_table: int
) -> Tuple[int, int, int]:
    """
    Given a table, it randomly finds a subtable which is used to sample the evidences

    :param evidence_per_table:
    :type evidence_per_table:
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

    selected_h = rng.choice(header_row_nums)  # 3

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
        if interval == 1 or interval < evidence_per_table:
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
