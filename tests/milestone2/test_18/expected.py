class Person:
    def __init__(self, name, age, weight):
        self.name = name
        self.age = age
        self.weight = weight
            
def slice_me():
    mahdi = Person('Mahdi', 25, 65)
    possible_ages = [10, 20, 30, 40, 50]
    mahdi.weight = mahdi.age * 2
    mahdi.age += possible_ages[2]
    mahdi.age *= mahdi.weight * possible_ages[3]
    return mahdi.age # slicing criterion

slice_me()