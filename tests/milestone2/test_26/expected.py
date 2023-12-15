class Person:
    def __init__(self, name):
        self.name = name

def slice_me():
    p2 = Person('Nobody')
    return p2.name # slicing criterion

slice_me()