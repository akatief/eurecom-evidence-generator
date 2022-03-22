from abc import abstractmethod


class TextualClaim:
    def __init__(self,
            evidence):
        '''
        Initializes a TextualClaim object.

        :param evidence: Evidence to generate a claim from
        '''
        self.evidence = evidence

    def getEvidence(self):
        return self.evidence

    @abstractmethod
    def __str__(self):
        '''
        Generates a textual claim based on provided evidence

        :return: A textual claim
        '''
        """
        Returns:
        """
        raise NotImplementedError("Must have implemented this.")