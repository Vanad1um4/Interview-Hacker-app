import json


def write_to_file(filename, data, add=True):
    try:
        mode = 'a' if add else 'w'
        with open(filename, mode, encoding='utf-8') as f:
            if isinstance(data, (list, dict)):
                f.write(json.dumps(data, ensure_ascii=False, indent=4) + '\n')
            else:
                f.write(str(data) + '\n')
    except:
        pass
