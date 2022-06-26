from typing import List, Tuple, Any
import numpy as np
import spacy
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable
from ..utils import TableException
from ..utils import TableExceptionType


def relational_table(tbl: WikiTable,
                     table_len: int,
                     rng: np.random.Generator,
                     evidence_per_table: int,
                     column_per_table: int,
                     key_strategy: str = 'random'
                     ) -> Tuple[List[List[Cell]], List[Cell], List[List[Cell]]]:
    """
    RANDOMLY  extract the evidence from the relational table.
    Example:
        selected_evidences = [['Totti', 128], ['Cassano', 103], ...]
        selected_h_cells = ['name', 'scored_gol']
        alternative_pieces = [ ['Totti', 'Cassano'], [128, 103]]

    :param tbl: The table to be scanned
    :param table_len: the len of the table
    :param rng: used to randomly extract cells
    :param evidence_per_table: how many Evidences from the same table
    :param column_per_table: how many cells for 1 Evidence
    :param key_strategy: heuristic for selecting the key column. Can be 'first',
                         'sensible' or None

    :return selected_evidences: [ ['Totti', 128], ['Cassano', 103], ...]
    :return selected_h_cells: ['name', 'scored_gol']
    :return alternative_pieces: the swappable cells for each header
    """

    # 0 for first table, 1 for second table, ...
    tbl_id = int(tbl.get_id().split('_')[1])
    try:
        # extract sub relational table
        index, start_row, end_row = sub_relational_table(
            tbl, rng=rng,
            table_len=table_len,
            evidence_per_table=evidence_per_table
        )
    except TableException:
        raise

    tbl_headers = tbl.get_header_rows()[index]

    # Now we have the range of correct rows associated to that specific header
    # from [start_i + 1,  end_i ]

    # randomly choose the evidence headers in the selected header
    list_cols = _get_cols_with_strategy(key_strategy=key_strategy,
                                        rng=rng,
                                        tbl=tbl,
                                        tbl_headers_len=len(tbl_headers.row),
                                        column_per_table=column_per_table,
                                        start_row=start_row,
                                        end_row=end_row)

    selected_h_cells = np.array(tbl_headers.row)[list_cols]

    # Now that we have the columns we randomly select #evidence_per_table rows
    possible_rows = np.arange(start_row + 1, end_row)

    # not enough rows to select
    if len(possible_rows) < evidence_per_table:
        raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

    # extract possible cells for generating negative samples
    # may crash if cell_id not in table
    alternative_pieces = [[] for _ in list_cols]
    try:
        alternative_pieces = extract_alternative_pieces(list_cols,
                                                        possible_rows,
                                                        tbl,
                                                        tbl_id)
    except KeyError:
        pass  # not raise error because may use it for SUPPORT Evidence

    # selected rows from subtable possible rows
    # remove the rows where at least one of the cell is empty
    # shape alternative_pieces (num_col, possible_rows)
    # this masks contains the row that have all the cells to be extractable (no empty,...)
    mask = [(p != -1).all() for p in np.array(alternative_pieces).T]
    possible_rows = possible_rows[mask]
    if len(possible_rows) == 0:
        raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

    list_rows = rng.choice(possible_rows,
                           evidence_per_table,
                           replace=False)

    selected_evidences = []
    for row in list_rows:  # For each row
        evidence = []
        for col in list_cols:  # For each column
            try:
                evidence += [tbl.get_cell(f'cell_{tbl_id}_{row}_{col}')]
            except KeyError:
                raise TableException(TableExceptionType.ID_NOT_COMPLIANT,
                                     tbl.page)
        selected_evidences.append(evidence)

    return selected_evidences, selected_h_cells, alternative_pieces


def extract_alternative_pieces(list_cols: List[int],
                               possible_rows: List[int],
                               tbl: WikiTable,
                               tbl_id: int):
    """
    It extracts the possible cell that may be used for swapping in case of REFUTED claim
    If the context cell is empty, the possible pieces contains -1

    :param list_cols: the list of selected header cell indexes
    :param possible_rows: the indexes of the rows in the subtable
    :param tbl: the analyzed WikiTable
    :param tbl_id: the id of the table inside the WikiPage

    :return: the swappable cells for each header
            possible_pieces = [ ['Totti', 'Cassano'], [128, 103] ]
    """
    # all_cells = [for cell_id in tbl.all_cells]
    alternative_pieces = []
    for j in list_cols:

        column_evidence_pieces = []
        for i in possible_rows:
            piece = tbl.get_cell(f'cell_{tbl_id}_{i}_{j}')
            if piece.content != "":
                column_evidence_pieces += [piece]
            else:
                column_evidence_pieces += [-1]

        alternative_pieces.append(column_evidence_pieces)
    return alternative_pieces


def sub_relational_table(tbl: WikiTable,
                         rng: np.random.Generator,
                         table_len: int,
                         evidence_per_table: int
                         ) -> Tuple[int, int, int]:
    """
    Given a table, it randomly finds a subtable which is used to sample the evidences

    :param evidence_per_table:
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


def _get_cols_with_strategy(key_strategy: str,
                            rng: np.random.Generator,
                            tbl: WikiTable,
                            tbl_headers_len: int,
                            column_per_table: int,
                            start_row: int,
                            end_row: int) -> List[int]:
    """
    Uses the chosen strategy to select the columns to generate claims from

    :param key_strategy:
    :param rng: random numpy generator
    :param tbl: tbl to which extract the subtable
    :param tbl_headers_len: length in cells of the header row
    :param column_per_table: number of columns to be chosen
    :param start_row: starting row for scoring analysis
    :param end_row: end row for scoring analysis

    """
    possible = list(range(tbl_headers_len))
    # if the number of columns matches the available ones
    # return all columns
    if tbl_headers_len <= column_per_table:
        return possible

    if key_strategy == 'first':
        list_cols = [possible.pop(0)] + rng.choice(possible,
                                                   column_per_table - 1,
                                                   replace=False).tolist()
    elif key_strategy == 'sensible':
        # start_row + 1 is passed to skip the header
        list_cols = [possible.pop(
            _key_sensible(tbl, tbl_headers_len, start_row + 1, end_row))] \
                    + rng.choice(possible,
                                 column_per_table - 1,
                                 replace=False).tolist()

    elif key_strategy == 'entity':
        # start_row + 1 is passed to skip the header
        list_cols = [possible.pop(
            _key_entity(tbl, tbl_headers_len, start_row + 1, end_row))] \
                    + rng.choice(possible,
                                 column_per_table - 1,
                                 replace=False).tolist()

    elif key_strategy == 'random':
        # randomly choose the evidence headers in the selected header
        list_cols = rng.choice(possible,
                               column_per_table,
                               replace=False).tolist()
    else:
        raise ValueError("Invalid choice of key detection strategy.")
    return list_cols


def _key_sensible(table: WikiTable,
                  n_cols: int,
                  start_row: int,
                  end_row: int):
    """
    Check table for all columns without duplicates and select one
    using heuristic based on data type and distance from left column

    :param table: The table to detect the key from
    :param header: The selected header of the subtable
    :param start_row: Row to begin analysis from
    :param end_row: Row to end analysis at
    """
    table_id = int(table.get_id().split('_')[1])
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
                    types.append(_get_type(table.get_cell(cell_id).content))
        # TODO: think about removing check on unicity
        if len(set(values)) == len(
                values):  # If col contains no duplicates appends it to candidates
            col_type = _col_type(types)
            candidates_scores.append(_get_type_score(col, col_type))
    if len(candidates_scores) == 0:  # If no columns are without duplicates defaults to first column
        return 0
    return np.argmax(candidates_scores)


# TODO: refactor to avoid duplicating code
def _key_entity(table: WikiTable,
                n_cols: int,
                start_row: int,
                end_row: int):
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
                labels += [doc.ent_type_ for doc in NER(table.get_cell(cell_id).content)]

        if len(set(values)) == len(
                values):  # If col contains no duplicates appends it to candidates
            candidates_scores.append(_get_entity_score(col, labels))
    if len(candidates_scores) == 0:  # If no columns are without duplicates defaults to first column
        return 0
    return np.argmax(candidates_scores)


def _get_type(n: Any):
    if n.isdigit():
        return int
    else:
        try:
            float(n)
            return float
        except ValueError:
            return str


def _col_type(types: List[Any]):
    col_type = int
    for t in types:
        if col_type is int and (t is float or t is str):
            col_type = t
        elif col_type is float and t is str:
            col_type = t
        else:
            break
    return col_type


def _get_type_score(col: int,
                    type: Any):
    """
    Returns a score based on column position in table
    and type. The closer a column is to the left border
    the higher its score is. Strings score highest, followed
    by ints and floats.
    """
    if type is str:
        type_mult = 1
    elif type is int:
        type_mult = 0.3
    else:  # float
        type_mult = 0.1
    return type_mult / (col + 1)


def _get_entity_score(col: int,
                      labels: List[str]):
    """
    Returns a score based on column position in table
    and Entity. The closer a column is to the left border
    the higher its score is. A heuristics assigns a score
    to different types of entity
    """
    score = 0
    n_rows = len(labels)
    for l in labels:
        if l in ['EVENT', 'FAC', 'LAW', 'NORP', 'ORG', 'PERSON', 'PRODUCT',
                 'WORK_OF_ART']:
            # Score normalized by number of rows
            score += 1 / n_rows
        elif l in ['LANGUAGE', 'GPE', 'LOC']:
            score += 0.3 / n_rows
        elif l in ['CARDINAL', 'DATE', 'MONEY', 'ORDINAL', 'PERCENT', 'QUANTITY', 'TIME']:
            score += 0.1 / n_rows
    return score / (col + 1)
