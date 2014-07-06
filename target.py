
import sub as SUB
import sub2



b = [2, 3]
c = [(4, 5), (6, 7)]
d = (8, [9, 10])
e = [d, d]

[f, g] = [1, 2]
[h, i] = [3, 4], 5
[j, k], m = h, i


def fun(x):
    def inner_fun(y=x):
        return y

    r = inner_fun()
    return r

fun(0)


#t(2, 4, *(4,))
#u = tuple(xrange(3))
#u = sum(4)
#v = tuple(xrange(3))
#u = sum((1, 2, 3))
#t(2.)


#g = lambda: None
    #return 2




