import re
from typing import List


def clean_content(content: str):
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


def get_context(caption: List,
                title: str) -> List[str]:
    # the caption it has already been generated
    if isinstance(caption[0], str):
        return caption

    return [
        f'{title}{s.get_id()}' if str(s.get_id()).startswith('_')
        else f'{title}_{s.get_id()}'
        for s in caption
    ]
