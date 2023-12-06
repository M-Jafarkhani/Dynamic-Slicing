class Person:
    def __init__(self, name, age, weight):
        self.name = name
        self.age = age
        self.weight = weight
            
def slice_me():
    mahdi = Person('Reza', 45, 80)
    return mahdi.age # slicing criterion

slice_me()