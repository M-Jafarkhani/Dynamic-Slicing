def slice_me():
    ages = [0, 25, 50, 75, 100]
    smallest_age = ages[0]
    middle_age = ages[2]
    highest_age = ages[-1]
    ages[-1] += ages[2] + smallest_age
    return ages # slicing criterion

slice_me()