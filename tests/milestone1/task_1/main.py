# DYNAPYT: DO NOT INSTRUMENT


import dynapyt.runtime as _rt

_dynapyt_ast_ = "/Users/mahdijafarkhani/Documents/Master's/Semester 02/PA/Dynamic-Slicing/tests/milestone1/task_1/main.py" + ".orig"
try:
    def slice_me():
        x = _rt._write_(_dynapyt_ast_, 1, 1, [lambda: x])
        y = _rt._write_(_dynapyt_ast_, 2, 2, [lambda: y])
        x = _rt._write_(_dynapyt_ast_, 5, _rt._read_(_dynapyt_ast_, 3, lambda: x) + _rt._read_(_dynapyt_ast_, 4, lambda: y), [lambda: x]) 
        z = _rt._write_(_dynapyt_ast_, 8, _rt._read_(_dynapyt_ast_, 6, lambda: x) - _rt._read_(_dynapyt_ast_, 7, lambda: y), [lambda: z])
        z = _rt._write_(_dynapyt_ast_, 9, 1, [lambda: z])
        x *= _rt._aug_assign_(_dynapyt_ast_, 10, lambda: x, 9, 4)
        y += _rt._aug_assign_(_dynapyt_ast_, 31, lambda: y, 0, 2 + _rt._read_(_dynapyt_ast_, 30, lambda: z)) # slicing criterion
        x = _rt._write_(_dynapyt_ast_, 12, 0, [lambda: x])    
        z = _rt._write_(_dynapyt_ast_, 14, _rt._read_(_dynapyt_ast_, 13, lambda: y), [lambda: z])
        y = _rt._write_(_dynapyt_ast_, 16, _rt._read_(_dynapyt_ast_, 15, lambda: x), [lambda: y])
        return _rt._read_(_dynapyt_ast_, 17, lambda: y) 
    
    _rt._read_(_dynapyt_ast_, 18, lambda: slice_me)()
except Exception as _dynapyt_exception_:
    _rt._catch_(_dynapyt_exception_)
