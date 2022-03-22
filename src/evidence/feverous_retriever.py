from abc import ABC
from . import EvidenceRetriever


class FEVEROUSRetriever(EvidenceRetriever, ABC):
    '''
    Retrieves evidence specifically from the FEVEROUS DB.
    '''
    def retrieve(self,
            data):
        '''
        Scans whole FEVEROUS dataset and returns list of Evidence objects.

        :param data: data to retrieve evidence from
        :return: a list of Evidence objects
        '''
        #TODO: implement table parsing
        # Naive way: consider only well formatted tables with headers on top
        return []