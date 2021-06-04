import os
import json
from hashlib import md5
import multiprocessing as mp
from tree_sitter import Language, Parser
from src.text_processor import text_processor

def mp_code_reader(code_base_path, file_type, storage_path):

    added_files, deleted_files, modified_files = filter_files(code_base_path, file_type, storage_path)

    if os.path.exists(os.path.join(storage_path, "code_data.json")):
        with open(os.path.join(storage_path, "code_data.json"), "r") as f:
            code_data = json.load(f)
    else:
        code_data = {}

    if len(added_files):
        pool = mp.Pool(mp.cpu_count())
        for code_file in added_files:
            pool.apply_async(added_files_reader, args=(code_file[0], code_file[1]), callback=code_data.update)
        pool.close()
        pool.join()

    if len(modified_files):
        pool = mp.Pool(mp.cpu_count())
        for code_file in modified_files:
            pool.apply_async(modified_files_reader, args=(code_file[0], code_file[1], code_data), callback=code_data.update)
        pool.close()
        pool.join()
    
    with open(os.path.join(storage_path, "code_data.json"), "w") as f:
        json.dump(code_data, f)

    return code_data, added_files, deleted_files, modified_files

def filter_files(code_base_path, file_type, storage_path):

    added_files = []
    deleted_files = []
    modified_files = []
    code_files = []
    
    dir_path = os.walk(code_base_path)
    for parent_dir, dir_name, file_names in dir_path:
        for file_name in file_names:
            if file_name.split(".")[-1].strip() in file_type:
                code_files.append(os.path.join(parent_dir, file_name))
    
    if os.path.exists(os.path.join(storage_path, "code_data.json")):
        with open(os.path.join(storage_path, "code_data.json"), "r+") as f:
            code_data = json.load(f)

            for file_path in list(code_data.keys()):
                if not file_path in code_files:
                    deleted_files.append(file_path)
                    del code_data[file_path]

            for code_file in code_files:
                if not code_file in code_data.keys():
                    added_files.append([code_file, code_file.split(".")[-1].strip()])
                else:
                    code_cont = open(code_file)
                    md5_val = md5(code_cont.read().encode()).hexdigest()
                    code_cont.close()
                    
                    if not md5_val == code_data[code_file]["md5"]:
                        code_data[code_file].update({"md5": md5_val})
                        modified_files.append([code_file, code_file.split(".")[-1].strip()])

            f.seek(0)
            f.truncate(0)
            json.dump(code_data, f)
    else:
        for code_file in code_files:
            added_files.append([code_file, code_file.split(".")[-1].strip()])
    
    return added_files, deleted_files, modified_files

def added_files_reader(code_file, file_type):
    
    code_data = {}

    with open(code_file) as f:
        if os.path.getsize(code_file):
            code_cont = f.read()
            md5_val = md5(code_cont.encode()).hexdigest()
            code_data[code_file] = {"content": text_processor(code_parser(code_cont, file_type)), "md5": md5_val}
            
    return code_data

def modified_files_reader(code_file, file_type, original_data):
    
    code_data = {}

    with open(code_file) as f:
        if os.path.getsize(code_file):
            code_cont = f.read()
            code_data[code_file] = {"content": text_processor(code_parser(code_cont, file_type)), "md5": original_data[code_file]["md5"]}
    
    return code_data

def code_parser(code_cont, file_type):

    if file_type == "py":
        file_type = "python"
    
    parser = Parser()
    parser.set_language(Language('./lib/languages.so', file_type))

    parsed_code = str.encode(code_cont)
    tree = parser.parse(parsed_code)
    code_lines = code_cont.split('\n')

    identifier = ""
    nodes = [tree.root_node]
    while nodes:
        temp = []
        for node in nodes:
            for child in node.children:
                temp.append(child)
                if(child.type == "identifier"):
                    identifier += code_lines[child.start_point[0]][child.start_point[1]:child.end_point[1]] + " "
        nodes = temp

    return code_cont + identifier
