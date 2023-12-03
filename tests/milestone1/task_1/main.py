# DYNAPYT: DO NOT INSTRUMENT


import dynapyt.runtime as _rt

_dynapyt_ast_ = "/Users/mahdijafarkhani/Documents/Master's/Semester 02/PA/Dynamic-Slicing/tests/milestone1/task_1/main.py" + ".orig"
try:
    def slice_me():
        _rt._func_entry_(_dynapyt_ast_, 45, [], "slice_me")
        ages = _rt._write_(_dynapyt_ast_, 1, [0, 25, 50, 75, 100], [lambda: ages])
        smallest_age = _rt._write_(_dynapyt_ast_, 4, _rt._sub_(_dynapyt_ast_, 3, _rt._read_(_dynapyt_ast_, 2, lambda: ages), [0]), [lambda: smallest_age])
        middle_age = _rt._write_(_dynapyt_ast_, 7, _rt._sub_(_dynapyt_ast_, 6, _rt._read_(_dynapyt_ast_, 5, lambda: ages), [2]), [lambda: middle_age])
        highest_age = _rt._write_(_dynapyt_ast_, 10, _rt._sub_(_dynapyt_ast_, 9, _rt._read_(_dynapyt_ast_, 8, lambda: ages), [-1]), [lambda: highest_age])
        ages[-1] += _rt._aug_assign_(_dynapyt_ast_, 69, lambda: _rt._sub_(_dynapyt_ast_, 59, _rt._read_(_dynapyt_ast_, 56, lambda: ages), [-1]), 0, _rt._sub_(_dynapyt_ast_, 62, _rt._read_(_dynapyt_ast_, 60, lambda: ages), [2]) + _rt._read_(_dynapyt_ast_, 68, lambda: smallest_age))
        return _rt._read_(_dynapyt_ast_, 64, lambda: ages) # slicing criterion
        _rt._func_exit_(_dynapyt_ast_, 45, "slice_me")
    
    _rt._read_(_dynapyt_ast_, 65, lambda: slice_me)()
except Exception as _dynapyt_exception_:
    _rt._catch_(_dynapyt_exception_)
