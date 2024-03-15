
def read_mapping_zh_en():
    dict_map = {}
    with open("metadata/mapping_zh_en.csv") as f:
        lines = [line.strip(" \n").split(",") for line in f.readlines() if line.strip() != "" and line.count(",") == 1]
    
    for line in lines:
        zh_text = line[0]
        en_text = line[1]
        if zh_text not in dict_map:
            dict_map[zh_text] = en_text
    
    return dict_map