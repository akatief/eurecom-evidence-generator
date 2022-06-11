from typing import List, Tuple, Union

import numpy as np
from feverous.utils.wiki_table import Cell
from feverous.utils.wiki_page import WikiTable
from ....logger import logger

from ...evidence import EvidencePiece
from ..feverous_retriever import FeverousRetriever
from ..utils import TableExceptionType
from ..utils import TableException
from ...utils import clean_content


class FeverousRetrieverEntropy(FeverousRetriever):

    # TODO: REFACTOR TO MOVE THIS UP IN feverous_retriever.py
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
        # returns multiple Row that are headers
        headers = tbl.get_header_rows()

        # no headers at all in the table
        if len(headers) == 0 and len(header_left) == 0:
            raise TableException(TableExceptionType.NO_HEADERS, tbl.page)

        # not enough columns in the Relational table
        if len(headers) != 0 and len(headers[0].row) <= self.column_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)
        # not enough columns in the entity table
        if len(header_left) != 0 and len(header_left) <= self.column_per_table:
            raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)

        try:
            # Not header on the left
            if len(header_left) == 0:
                output = entropy_relational_table(tbl, self.evidence_per_table, self.column_per_table)
            else:
                output = entropy_entity_table(tbl, self.evidence_per_table, self.column_per_table)

        except TableException:
            raise  # propagate up the TableException

        selected_cells, selected_h_cells, alternative_pieces = output
        if self.verbose:
            logger.info(
                f"Page: {tbl.page} {tbl.get_id()} Selected headers: {[str(cell) for cell in selected_h_cells]}".encode(
                    "utf-8"))
        evidences = []
        for evidence_idx, evidence in enumerate(selected_cells):
            local_evidences = []
            for cell_idx, cell in enumerate(evidence):
                local_evidences.append(
                    EvidencePiece(tbl.page,
                                  tbl.caption,
                                  cell,
                                  selected_h_cells[evidence_idx][cell_idx],
                                  alternative_pieces[evidence_idx][cell_idx]
                                  )
                )
            evidences.append(local_evidences)

        return evidences


def entropy_relational_table(tbl: WikiTable,
                             evidence_per_table: int,
                             column_per_table: int,
                             ) -> Tuple[List[List[Cell]], List[List[Cell]], List[List[List[Cell]]]]:
    """
    Extracts evidence sets from a table using an entropy heuristic.

    :param tbl: The table to be scanned
    :param evidence_per_table: how many Evidences from the same table
    :param column_per_table: how many cells for 1 Evidence

    :return selected_cells: [ ['Totti', 128], ['Cassano', 103], ...]
    :return selected_h_cells: [ ['name', 'scored_gol'], ['name', 'scored_gol'], ...]
    :return possible_pieces: the swappable cells for each header
    """
    # Parse table into matrix
    matrix_table = _table_to_matrix(tbl)
    return _generic_table(matrix_table,tbl,evidence_per_table,column_per_table)


def entropy_entity_table(tbl: WikiTable,
                         evidence_per_table: int,
                         column_per_table: int,
                         ) -> Tuple[List[List[Cell]], List[List[Cell]], List[List[List[Cell]]]]:
    """
    Extracts evidence sets from an entity table using an entropy heuristic.

    :param tbl: The table to be scanned
    :param evidence_per_table: how many Evidences from the same table
    :param column_per_table: how many cells for 1 Evidence

    :return selected_cells: [ ['Totti', 128], ['Cassano', 103], ...]
    :return selected_h_cells: [ ['name', 'scored_gol'], ['name', 'scored_gol'], ...]
    :return possible_pieces: list of possible replacement cells for each evidence in selected_cells
    """
    matrix_table = _table_to_matrix(tbl)
    # Transpose matrix
    matrix_table = _transpose_matrix_table(matrix_table)
    return _generic_table(matrix_table,tbl,evidence_per_table,column_per_table)


def _generic_table(matrix_table: List[List[Cell]],
                   tbl: WikiTable,
                   evidence_per_table: int,
                   column_per_table: int,
                   ) -> Tuple[List[List[Cell]], List[List[Cell]], List[List[List[Cell]]]]:

    n_cols = len(matrix_table[0])
    if n_cols < column_per_table:
        raise TableException(TableExceptionType.NO_ENOUGH_COL, tbl.page)

    # Find sub-tables
    subtables = _split_sub_tables(matrix_table)
    evidences = []
    evidence_entropies = []
    headers = []
    alternatives = []
    # Scan subtables, generate entropy map for their columns,
    # and extract as much evidence as possible
    for subtable in subtables:
        np_subtable = _table_to_numpy(subtable)
        entropies = _get_table_entropies(np_subtable)
        partial_evidences, partial_headers, partial_entropy_scores, partial_alternatives = _extract_evidences(subtable,
                                                                                                              column_per_table,
                                                                                                              entropies)
        evidences += partial_evidences
        evidence_entropies += partial_entropy_scores
        headers += partial_headers
        alternatives += partial_alternatives
    if len(evidences) < evidence_per_table:
        raise TableException(TableExceptionType.NO_ENOUGH_ROW, tbl.page)

    max_entropy_indices = np.argpartition(np.array(evidence_entropies), -evidence_per_table)[-evidence_per_table:]

    selected_evidences = [evidences[i] for i in max_entropy_indices]
    selected_headers = [headers[i] for i in max_entropy_indices]
    selected_alternatives = [alternatives[i] for i in max_entropy_indices]

    return selected_evidences, selected_headers, selected_alternatives


def _table_to_matrix(table: WikiTable) -> List[List[Union[Cell, None]]]:
    """
    Transforms a table into an ordered matrix with eventual empty cells.

    :param table: the table to generate the list from
    :return: a list of lists of cells
    """
    n_rows, n_cols = _table_size(table)
    cells = [[None for c in range(n_cols)] for r in range(n_rows)]
    for cell_id in table.get_ids():
        if 'caption' in cell_id:
            continue
        if 'header' in cell_id:  # header_cell_table_row_column
            col = int(cell_id.split('_')[4])
            row = int(cell_id.split('_')[3])
        else:  # cell_table_row_column
            col = int(cell_id.split('_')[3])
            row = int(cell_id.split('_')[2])
        cell = table.get_cell(cell_id)
        # Filters out empty cells marking them as None
        if _is_valid_content(cell.content):
            cells[row][col] = cell
        else:
            cells[row][col] = None

    return cells


def _table_size(table: WikiTable):
    row_ids = [int(cell_id.split('_')[3]) for cell_id in table.get_ids() if 'header' in cell_id]
    row_ids += [int(cell_id.split('_')[2]) for cell_id in table.get_ids() if 'header' not in cell_id and 'caption' not in cell_id]
    n_rows = max(row_ids) + 1

    col_ids = [int(cell_id.split('_')[4]) for cell_id in table.get_ids() if 'header' in cell_id]
    col_ids += [int(cell_id.split('_')[3]) for cell_id in table.get_ids() if 'header' not in cell_id and 'caption' not in cell_id]
    n_cols = max(col_ids) + 1

    return n_rows, n_cols

def _split_sub_tables(table: List[List[Union[Cell, None]]]) -> List[List[List[Union[Cell, None]]]]:
    """
    Split a table in matrix form into subtables
    based on header rows. Only the last header in each subtable is kept

    :param table: the table to be split
    :return: a list of tables
    """
    subtables = []
    current_subtable = []
    for row in table:
        # Check if row contains at least one header cell
        header_row = sum([cell.is_header for cell in row if cell is not None]) > 0
        if header_row:
            if len(current_subtable) > 1:
                subtables.append(current_subtable)
            current_subtable = []
        current_subtable.append(row)
    subtables.append(current_subtable)
    return subtables


def _get_table_entropies(np_table) -> List[float]:
    """
    Computes entropy for each column of given table.

    :param np_table: table parsed in numpy format with _table_to_numpy method
    :return: list of entropy values computed over columns
    """
    # get numpy table but skip first header column
    np_table = np_table[1:, :]
    n_rows = len(np_table)
    entropies = []
    for column in np_table.T:
        _, counts = np.unique(column, return_counts=True)
        entropy = np.mean(-np.log2(counts / n_rows))
        entropies.append(entropy)
    return entropies


def _table_to_numpy(table):
    """
    Converts table from list of lists format into string np.ndarray format
    replacing None values with ''

    :param table: table to be parsed
    :return: numpy ndarray table
    """
    # Cast Cell matrix to str and transforms None into ''
    str_table = [[clean_content(cell.content) if cell is not None else '' for cell in row] for row in table]
    return np.array(str_table)


def _extract_evidences(table_matrix, columns_per_table, column_entropies):
    """
    Extracts all sets of columns_per_table adjacent cells
    and uses entropy per column to extract and select meaningful
    evidences

    :param table_matrix: table in matrix (list of list of cell) format
    :param columns_per_table: columns composing each evidence, length of evidence
    :param column_entropies: list of entropies for each column
    """
    n_cols = len(table_matrix[0])
    # Get transposed matrix without headers
    transposed = _transpose_matrix_table(table_matrix[1:])
    transposed = _clean_matrix_table(transposed)
    evidences = []
    headers = []
    entropy_scores = []
    alternatives = []
    for row in table_matrix[1:]:  # skip header row
        for i in range(n_cols - columns_per_table + 1):
            # List of columns_per_table Cells
            matrix_slice = row[i:i + columns_per_table]
            header_slice = table_matrix[0][i:i + columns_per_table]
            alternative_slice = transposed[i:i + columns_per_table]
            flattened_alt_slice = list(np.concatenate(alternative_slice).flat)
            if None not in matrix_slice and None not in header_slice and len(flattened_alt_slice) > 0:
                evidences.append(matrix_slice)
                entropy_slice = column_entropies[i:i + columns_per_table]
                entropy_scores.append(sum(entropy_slice))
                headers.append(header_slice)

                alternatives.append(alternative_slice)
    return evidences, headers, entropy_scores, alternatives


def _transpose_matrix_table(matrix_table):
    """
    Transposes a matrix in form List[List[Any]]
    """
    return list(map(list, zip(*matrix_table)))


def _clean_matrix_table(matrix_table):
    """
    Removes all occurrences of None in matrix in form List[List[Any]]
    """
    return [list(filter(None, row)) for row in matrix_table]

def _is_valid_content(content):
    """
    Checks if Cell content is a valid string or an empty value.
    Es: '---' --> False
        'John Cena' --> True
    """
    return any(c.isdigit() for c in content) or any(c.isalpha() for c in content)

def print_table_matrix(table_matrix):
    for row in table_matrix:
        print([str(cell) for cell in row])
