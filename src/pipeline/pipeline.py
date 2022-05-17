from abc import abstractmethod


class PipelineElement:
    """
    Defines a block of a ClaimGeneratorPipeline. __cell__ method takes all arguments,
     executes the main function of the
    block and returns the input of the next.
    """

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError("Must have implemented this.")

    def __len__(self):
        return 1

    def __iter__(self):
        return iter([self])

class ClaimGeneratorPipeline:
    """
    Runs a claim generation task starting from raw data all the way to textual claims.
    Pipeline is made of PipelineElements that are run in sequence.
    Each PipelineElement can be a list of PipelineElement, in this case ClaimGeneratorPipeline
    will be run in parallel on each one and the results will be concatenated.
    An element output is the input of the next.
    """

    def __init__(self, elements):
        self.elements = elements

    @abstractmethod
    def generate(self, input=None):
        """
        Runs the whole pipeline on the provided table.

        :param self
        :param table: table to retrieve textual claims from.
        :param header_content: if True, return the header inside the content
        :returns A list of textual claims
        """
        next_input = input
        # Calls __call__ method for each element in sequence
        for pip_element in self.elements:
            element_output = []
            for paral_element in pip_element:
                element_output += paral_element(next_input)
            next_input = element_output
        pipeline_output = next_input
        return pipeline_output
