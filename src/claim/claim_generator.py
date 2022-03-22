from abc import abstractmethod
from ..evidence import Evidence
from ..claim import TextualClaim
from ..pipeline import PipelineElement

class TextualClaimGenerator(PipelineElement):
    '''
    Element generating textual claims starting from Evidence objects.
    '''
    def __init__(self):
        return

    @abstractmethod
    def generate(self,
            evidence: [list[Evidence]]):
        '''
        Generate textual claims based on evidence

        :param evidence: a list of evidence objects
        :return: a list of TextualClaim objects
        '''
        raise NotImplementedError("Must have implemented this.")