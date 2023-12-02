def slice_me():
    x = 1
    y = 2
    x = x + y 
    z = x - y
    z = 1
    x *= 4
    y += 2 + z # slicing criterion
    x = 0    
    z = y
    y = x
    return y 

slice_me()