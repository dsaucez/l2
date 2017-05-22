import socket
import random
import time

N = 100

l = list()

for i in xrange(0, N):
   l.append (int(random.random()*10))


def process(l):
   l2 = l
   l2.sort()
   return l2

i = 0
while(len(l) > 0
   i = i+1
   l = process(l)
   l = filter(lambda x: random.random() >.5, l)
print i
