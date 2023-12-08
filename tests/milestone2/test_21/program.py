class Person:
    def __init__(self, name, age, weight, append):
        self.name = name
        self.age = age
        self.weight = weight
        self.append = append
            
def slice_me():
    mahdi = Person('Mahdi', 25, 65, 'Dummy Attribute')
    possible_ages = [10, 20, 30, 40, 50]
    mahdi.name = 'Mehdi'
    mahdi.weight = mahdi.age * 2
    mahdi.age += possible_ages[2]
    mahdi.age *= mahdi.weight * possible_ages[3]
    possible_ages.clear()
    mahdi.name = mahdi.append
    return mahdi.name # slicing criterion

slice_me()