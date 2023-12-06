class Person:
    def __init__(self, name, age, weight):
        self.name = name
        self.age = age
        self.weight = weight
            
def slice_me():
    mahdi = Person('Mahdi', 25, 65)
    mahdi.name = 'Mehdi'
    mahdi.weight = mahdi.age * 2
    mahdi.age += 10
    mahdi = Person('Reza', 45, 80)
    return mahdi.age # slicing criterion

slice_me()