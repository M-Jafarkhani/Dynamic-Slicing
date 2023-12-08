class Person:
    def __init__(self, name, age, weight, append):
        self.name = name
        self.age = age
        self.weight = weight
        self.append = append
            
def slice_me():
    mahdi = Person('Mahdi', 25, 65, 'Dummy Attribute')
    mahdi.name = mahdi.append
    return mahdi.name # slicing criterion

slice_me()