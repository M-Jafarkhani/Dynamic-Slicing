# DYNAPYT: DO NOT INSTRUMENT


import dynapyt.runtime as _rt

_dynapyt_ast_ = "/Users/mahdijafarkhani/Documents/Master's/Semester 02/PA/Dynamic-Slicing/tests/milestone1/task_1/main.py" + ".orig"
try:
    def slice_me():
        _rt._func_entry_(_dynapyt_ast_, 14, [], "slice_me")
        ages = _rt._write_(_dynapyt_ast_, 15, [0, 25, 50, 75, 100], [lambda: ages])
        smallest_age = _rt._write_(_dynapyt_ast_, 18, _rt._sub_(_dynapyt_ast_, 17, _rt._read_(_dynapyt_ast_, 16, lambda: ages), [0]), [lambda: smallest_age])
        middle_age = _rt._write_(_dynapyt_ast_, 21, _rt._sub_(_dynapyt_ast_, 20, _rt._read_(_dynapyt_ast_, 19, lambda: ages), [2]), [lambda: middle_age])
        highest_age = _rt._write_(_dynapyt_ast_, 24, _rt._sub_(_dynapyt_ast_, 23, _rt._read_(_dynapyt_ast_, 22, lambda: ages), [-1]), [lambda: highest_age])
        new_highest_age = _rt._write_(_dynapyt_ast_, 27, _rt._read_(_dynapyt_ast_, 25, lambda: middle_age) + _rt._read_(_dynapyt_ast_, 26, lambda: highest_age), [lambda: new_highest_age])
        _rt._attr_(_dynapyt_ast_, 29, _rt._read_(_dynapyt_ast_, 28, lambda: ages), "append")(_rt._read_(_dynapyt_ast_, 30, lambda: new_highest_age))
        return _rt._read_(_dynapyt_ast_, 31, lambda: ages) # slicing criterion
        _rt._func_exit_(_dynapyt_ast_, 14, "slice_me")
    
    _rt._read_(_dynapyt_ast_, 32, lambda: slice_me)()
except Exception as _dynapyt_exception_:
    _rt._catch_(_dynapyt_exception_)
