"""
Read locally stored bug reports and preprocess their text
"""

import xml.etree.ElementTree as ET
from src.text_processor import tokenizer

def bug_reader(bug_reports_path: str):
    """
    Parse bug reports in ".xml" file format, such as Bugzbook dataset.
    """

    bug_data = {}
    fixed_files = {}

    tree = ET.parse(bug_reports_path)
    root = tree.getroot()
    for child in root:
        bug_data[child.get("id")] = child[0].find("summary").text.lower()\  
                                + child[0].find("description").text.lower()
        fixed_files[child.get("id")] = child[1].find("file").text    
    bug_data = tokenizer(bug_data)
    return bug_data, fixed_files
