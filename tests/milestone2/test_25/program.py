def slice_me():
    x = [1,2,3,4,5]
    x[0] = 10
    y = 2
    z = x[0] + y
    x[0] = 20
    
    print(z)
    print(x) # slicing criterion
    print(y)

slice_me()