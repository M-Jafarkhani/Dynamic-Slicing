class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
            
def slice_me():
    mahdi = Person('Mahdi',25)
    mahdi.age += 10
    return mahdi.age # slicing criterion

slice_me()