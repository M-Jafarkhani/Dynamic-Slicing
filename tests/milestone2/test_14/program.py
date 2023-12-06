class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
            
def slice_me():
    mahdi = Person('Mahdi',25)
    mahdi.name = 'Mehdi'
    mahdi.age += 10
    return mahdi # slicing criterion

slice_me()