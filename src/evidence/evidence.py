import re


class EvidencePiece:
    """
    Contains a single piece of information pertaining to some Evidence.
    """
    # TODO: make it more general, not bound to table structure
    def __init__(self, wikipage, caption, cell, header_content):
        """
        cell id => cell_<table_id>_<row_num>_<column_num>
        """
        self.wiki_page = wikipage
        self.cell_id = cell.name
        self.table = cell.name.split('_')[1]
        self.row = cell.name.split('_')[2]
        self.column = cell.name.split('_')[3]

        self.caption = caption

        self.header_content = self._clean_content(header_content)

        # Added for the links in the table
        content = cell.content
        self.content = self._clean_content(content)

    def _clean_content(self, content):
        init_content = content
        content = content.replace('[H]', '')
        content = content.replace('\n', ' ')
        content = re.sub("(?<=\[\[)(.*?)(?=\|)",
                         '',
                         content)  # Matches all text between [[ and | and removes it
        content = content.replace('[[|', '')
        content = re.sub('(?<=\[)(.*?)(?=\])',
                         '',
                         content)  # Matches all text between [[ and ]] and removes it

        content = content.replace(']', '')  # Takes care of all [] and [[]]
        content = content.replace('[', '')

        return content

    def __str__(self):
        return f"{self.content} " \
               f"- {self.header_content} " \
               f"- {self.cell_id} -" \
               f" {', '.join([str(c) for c in self.caption])}"


class Evidence:
    """
    Contains pieces of evidence along with the template giving meaning.
    """

    def __init__(self,
                 evidence_pieces,
                 column_per_table,
                 label,
                 seed):
        """
        :param evidence_pieces: List of List of pieces of evidence
                                columns = sample header from the table
                                row = total number of evidence

        :param label: Defines the claim as either "SUPPORTS" or "REFUTES"
        :param template: The template with which the evidence was retrieved
        """
        self.evidence_pieces = evidence_pieces
        self.column_per_table = column_per_table
        self.seed = seed
        self.label = label

    def __str__(self):
        my_string = ''
        for e in self.evidence_pieces:
            my_string += f'{str(e)} | '

        return my_string + self.label

