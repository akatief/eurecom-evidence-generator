import re
from typing import List


def clean_content(content):
    """
    Cleans a cell content of formatting symbols introduced in FEVEROUS dataset

    :param content: cell content as read from FEVEROUS dataset
    :return: the cleaned cell content as string
    """
    content = content.replace('[H]', '')
    content = content.replace('\n', ' ')
    content = re.sub("(?<=\[\[)(.*?)(?=\|)",
                     '',
                     content)  # Matches all text between [[ and | and removes it
    content = content.replace('[[|', '')
    content = re.sub('(?<=\[)(.*?)(?=])',
                     '',
                     content)  # Matches all text between [[ and ]] and removes it

    content = content.replace(']', '')  # Takes care of all [] and [[]]
    content = content.replace('[', '')

    return content


def to_compact_text(evidence_pieces):
    """
    Converts evidence objects into strings the model can elaborate to generate
     a textual claim

    :return: text encoded in compact form.
             eg:
             'Washington && City && List of cities
             | 7.615 millions && Inhabitants && List of cities '
    """
    ep_to_text = lambda ep: ' && '.join([ep.content, ep.wiki_page, ep.header_content])
    textual_pieces = [ep_to_text(ep) for ep in evidence_pieces]
    return ' | '.join(textual_pieces)


def to_totto_text(evidence_pieces):
    """
    Converts evidence objects into strings
     the model can elaborate to generate a textual claim

    :return: text encoded in totto form.
             eg: <page_title> list of governors of south carolina </page_title>
              <section_title> governors under the constitution of 1868 </section_title>
              <table> <cell> 76 </cell>
              <cell> daniel henry chamberlain </cell>
               <cell> december 1, 1874 </cell> </table>
    """
    pieces = evidence_pieces
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

    # TODO: implement better management for title
    #  (eg: print every unique title across all EvidencePieces)
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


def get_context(
        caption: List,
        title: str
) -> List[str]:
    # the caption it has already been generated
    if isinstance(caption[0], str):
        return caption

    return [
        f'{title}{s.get_id()}' if str(s.get_id()).startswith('_')
        else f'{title}_{s.get_id()}'
        for s in caption
    ]
