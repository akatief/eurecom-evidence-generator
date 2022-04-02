from abc import ABC, abstractmethod


class Strategy(ABC):

    def __init__(self,
                 tbl_id,
                 tbl,
                 header_left,
                 table_len,
                 num_column,
                 num_evidence,
                 if_header,
                 rng):
        """

        :param tbl_id:
        :param tbl:
        :type tbl:
        :param header_left:
        :type header_left:
        :param table_len:
        :type table_len:
        :param num_column:
        :type num_column:
        :param num_evidence:
        :type num_evidence:
        :param if_header:
        :type if_header:
        :param rng:
        :type rng:
        """


        print('hello world')

    @abstractmethod
    def get_cells(self):
        pass
