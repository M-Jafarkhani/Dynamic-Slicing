import utils

file_path = 'samples/task2/main.py'
with open(file_path, 'r') as f:
    code = f.read()
lines_to_keep = [9,10,11,13] 
new_code = utils.remove_lines(code, lines_to_keep)
print(new_code)



