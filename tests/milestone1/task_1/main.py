# DYNAPYT: DO NOT INSTRUMENT


import dynapyt.runtime as _rt

_dynapyt_ast_ = "/Users/mahdijafarkhani/Documents/Master's/Semester 02/PA/Dynamic-Slicing/tests/milestone1/task_1/main.py" + ".orig"
try:
    class Person:
        def __init__(self, name, age, weight):
            _rt._func_entry_(_dynapyt_ast_, 0, [lambda: self, lambda: name, lambda: age, lambda: weight], "__init__")
            self.name = _rt._write_(_dynapyt_ast_, 2, _rt._read_(_dynapyt_ast_, 1, lambda: name), [lambda: self.name])
            self.age = _rt._write_(_dynapyt_ast_, 4, _rt._read_(_dynapyt_ast_, 3, lambda: age), [lambda: self.age])
            self.weight = _rt._write_(_dynapyt_ast_, 6, _rt._read_(_dynapyt_ast_, 5, lambda: weight), [lambda: self.weight])
            _rt._func_exit_(_dynapyt_ast_, 0, "__init__")
                
    def slice_me():
        _rt._func_entry_(_dynapyt_ast_, 7, [], "slice_me")
        mahdi = _rt._write_(_dynapyt_ast_, 9, _rt._read_(_dynapyt_ast_, 8, lambda: Person)('Mahdi', 25, 65), [lambda: mahdi])
        mahdi.name = _rt._write_(_dynapyt_ast_, 10, 'Mehdi', [lambda: mahdi.name])
        mahdi.weight = _rt._write_(_dynapyt_ast_, 13, _rt._attr_(_dynapyt_ast_, 12, _rt._read_(_dynapyt_ast_, 11, lambda: mahdi), "age") * 2, [lambda: mahdi.weight])
        mahdi.age += _rt._aug_assign_(_dynapyt_ast_, 16, lambda: _rt._attr_(_dynapyt_ast_, 15, _rt._read_(_dynapyt_ast_, 14, lambda: mahdi), "age"), 0, 10)
        mahdi = _rt._write_(_dynapyt_ast_, 18, _rt._read_(_dynapyt_ast_, 17, lambda: Person)('Reza', 45, 80), [lambda: mahdi])
        return _rt._attr_(_dynapyt_ast_, 20, _rt._read_(_dynapyt_ast_, 19, lambda: mahdi), "age") # slicing criterion
        _rt._func_exit_(_dynapyt_ast_, 7, "slice_me")
    
    _rt._read_(_dynapyt_ast_, 21, lambda: slice_me)()
except Exception as _dynapyt_exception_:
    _rt._catch_(_dynapyt_exception_)
