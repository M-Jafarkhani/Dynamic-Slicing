def slice_me():
    ages = [0, 25, 50, 75, 100]
    highest_age = ages[-1]
    ages.append(highest_age)
    return ages # slicing criterion

slice_me()