import re


class EvidencePiece:
    """
    Contains a single piece of information pertaining to some Evidence.
    """

    # TODO: make it more general, not bound to table structure
    # TODO: add argument comments
    def __init__(self, wikipage, caption, cell, header_cell):
        """
        cell id => cell_<table_id>_<row_num>_<column_num>
        """
        self.wiki_page = wikipage
        self.cell_id = cell.name
        self.cell = cell
        self.table = int(self.cell_id.split('_')[1])
        self.row = int(self.cell_id.split('_')[2])
        self.column = int(self.cell_id.split('_')[3])

        self.caption = caption

        self.header_content = EvidencePiece._clean_content(header_cell.content)
        self.header = header_cell

        # Added for the links in the table
        content = cell.content
        self.content = self._clean_content(content)

    # TODO: move it elsewhere (possibly in evidence_retriever)
    @staticmethod
    def _clean_content(content):
        '''
        Cleans a cell content of formatting symbols introduced in FEVEROUS dataset

        :param content: cell content as read from FEVEROUS dataset
        :return: the cleaned cell content as string
        '''
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

    def __eq__(self, other):
        return self.cell_id == other.cell_id

    def __lt__(self, other):
        if self.wiki_page is not other.wiki_page: return self.wiki_page < other.wiki_page
        if self.table is not other.table:
            return self.table < other.table
        elif self.row is not other.row:
            return self.row < other.row
        elif self.column is not other.column:
            return self.column < other.column
        else:
            return False


# TODO: add argument comments
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

    # TODO: make all methods static
    def _to_compact_text(self):
        '''
        Converts evidence objects into strings the model can elaborate to generate a textual claim

        :return: text encoded in compact form.
                 eg: 'Washington && City && List of cities | 7.615 millions && Inhabitants && List of cities '
        '''
        ep_to_text = lambda ep: ' && '.join([ep.content, ep.wiki_page, ep.header_content])
        textual_pieces = [ep_to_text(ep) for ep in self.evidence_pieces]
        return ' | '.join(textual_pieces)

    def _to_totto_text(self):
        '''
        Converts evidence objects into strings the model can elaborate to generate a textual claim

        :return: text encoded in totto form.
                 eg: <page_title> list of governors of south carolina </page_title> <section_title> governors under the constitution of 1868 </section_title> <table> <cell> 76 </cell> <cell> daniel henry chamberlain </cell> <cell> december 1, 1874 </cell> </table>
        '''
        pieces = self.evidence_pieces
        pieces.sort()

        t_start = '<table> '
        t_end = ' </table>'
        r_start = '<row> '
        r_end = ' </row>'
        c_start = ' <cell> '
        c_end = ' </cell>'
        h_start = ' <col_header> '
        h_end = ' </col_header> '
        title = ' <page_title> ' + pieces[0].wiki_page + ' </page_title> '

        # TODO: implement better management for title (eg: print every unique title across all EvidencePieces)
        text = title + t_start + r_start + c_start
        curr_table = pieces[0].table
        curr_row = pieces[0].row
        curr_column = pieces[0].column

        for p in pieces:
            if p.table != curr_table:
                text += c_end + r_end + t_end + t_start + r_start + c_start
                curr_table = p.table
                curr_row = p.row
                curr_column = p.column
            elif p.row != curr_row:
                text += c_end + r_end + r_start + c_start
                curr_row = p.row
                curr_column = p.column
            elif p.column != curr_column:
                text += c_end + c_start
                curr_column = p.column
            text += p.content + h_start + p.header_content + h_end

        text += c_end + r_end + t_end
        return text

    def to_text(self, encoding='compact'):
        '''
        Converts evidence objects into strings the model can elaborate to generate a textual claim.
        Uses selected encoding. Possible choices are 'compact' and 'totto'.

        :param encoding:
        :return: text encoded in chosen form.
        '''
        if encoding == 'compact':
            return self._to_compact_text()
        elif encoding == 'totto':
            return self._to_totto_text()
        else:
            raise ValueError('Invalid choice of encoding')

    def __str__(self):
        my_string = ''
        for e in self.evidence_pieces:
            my_string += f'{str(e)} | '

        return my_string + self.label
