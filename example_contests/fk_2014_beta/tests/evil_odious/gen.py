
import random

ts = [
    (1, 1),
    (2, 2),
    (3, 3),
    (5, 5),
    (10, 20),
    (100, 300),
    (1000, 3000),
    (10**3, 10**5),
    (10**4, 10**6),
    (10**5, 10**7),
    (10**6, 10**8),
    (10**7, 10**9),
    (10**9, 10**10),
    (10**10, 10**11),
    (10**11, 10**12),
    (10**12, 10**13),
    (10**14, 10**15),
    (10**14, 10**15),
    (1, 10**15),
    (1, 10**15),
    (1, 10**15),
    (1, 10**15),
]

for i, (a,b) in enumerate(ts):

    with open('%02d.in' % i, 'w') as f:
        f.write('%d\n' % random.randint(a, b))
