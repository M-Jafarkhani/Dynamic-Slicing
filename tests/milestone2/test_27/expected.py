class Person:
    def __init__(self, name):
        self.name = name

def slice_me():
    p1 = Person('Nobody')
    p2 = p1
    p1.name = 'Mahdi'
    return p2.name # slicing criterion

slice_me()