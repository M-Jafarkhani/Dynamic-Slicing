# DYNAPYT: DO NOT INSTRUMENT


import dynapyt.runtime as _rt

_dynapyt_ast_ = "/Users/mahdijafarkhani/Documents/Master's/Semester 02/PA/Dynamic-Slicing/tests/milestone2/test_7/program.py" + ".orig"
try:
    class Person:
        def __init__(self, name):
            _rt._func_entry_(_dynapyt_ast_, 0, [lambda: self, lambda: name], "__init__")
            self.name = _rt._write_(_dynapyt_ast_, 2, _rt._read_(_dynapyt_ast_, 1, lambda: name), [lambda: self.name])
            _rt._func_exit_(_dynapyt_ast_, 0, "__init__")
                
    def slice_me():
        _rt._func_entry_(_dynapyt_ast_, 3, [], "slice_me")
        p = _rt._write_(_dynapyt_ast_, 5, _rt._read_(_dynapyt_ast_, 4, lambda: Person)('Nobody'), [lambda: p])
        indefinite_pronouns = _rt._write_(_dynapyt_ast_, 6, ['Everybody', 'Somebody', 'Anybody'], [lambda: indefinite_pronouns])
        _rt._attr_(_dynapyt_ast_, 8, _rt._read_(_dynapyt_ast_, 7, lambda: indefinite_pronouns), "append")(_rt._attr_(_dynapyt_ast_, 10, _rt._read_(_dynapyt_ast_, 9, lambda: p), "name"))
        return _rt._attr_(_dynapyt_ast_, 12, _rt._read_(_dynapyt_ast_, 11, lambda: p), "name") # slicing criterion
        _rt._func_exit_(_dynapyt_ast_, 3, "slice_me")
    
    _rt._read_(_dynapyt_ast_, 13, lambda: slice_me)()
except Exception as _dynapyt_exception_:
    _rt._catch_(_dynapyt_exception_)
