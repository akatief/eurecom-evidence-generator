from abc import abstractmethod
from ..pipeline import PipelineElement


class EvidenceRetriever(PipelineElement):
    """
    Retrieves evidence from some data passed as input.
    """

    def __init__(self,
                 n_pieces: int,
                 verbose: bool = False):
        """
        :param n_pieces: Number of pieces of evidence to be returned.
        :param verbose: if True prints additional debug messages
        """
        self.n_pieces = n_pieces
        self.verbose = verbose

    @abstractmethod
    def retrieve(self):
        """
        Scans data and returns a list of Evidence objects

        :return: a list of Evidence objects
        """

        raise NotImplementedError("Must have implemented this.")

    def __call__(self, *args):
        return self.retrieve
