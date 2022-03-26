from abc import abstractmethod
from ..evidence import EvidenceRetriever
from ..claim import TextualClaim
from ..claim import TextualClaimGenerator


class PipelineElement:
    '''
    Defines a block of a ClaimGeneratorPipeline. __cell__ method takes all arguments, executes the main function of the
    block and returns the input of the next.
    '''
    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError("Must have implemented this.")

class ClaimGeneratorPipeline:
    '''
    Runs a claim generation task starting from raw data all the way to textual claims.
    Pipeline is made of PipelineElements that are run in sequence. An element output is the input of the next.
    '''
    def __init__(self, elements):
        self.elements = elements

    @abstractmethod
    def generate(self, table):
        """
        Runs the whole pipeline on the provided table

        :param self
        :param table: table to retrieve textual claims from.
        :returns A list of textual claims
        """
        next_input = table
        # Calls __call__ method for each element in sequence
        for e in self.elements:
            next_input = e(next_input)
        output = next_input
        return output