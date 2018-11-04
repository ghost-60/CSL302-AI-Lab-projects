import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.io as sio
import numpy as np
import operator
import skimage.io as skio

from random import randint
from collections import defaultdict

import math
import heapq

import networkx as nx

def ProcessPQ(joints, marg, feature_length):
  """
  Populates a heap in descending order of mutual informations.
  This is used to build the maximum spanning tree.
  Contains mutual information of every feature with respect to every other feature
  """
  #variable defining the heap
  pq = []

  for i in range(feature_length):
    for j in range(i+1, feature_length):
      I = 0
      for x_u, p_x_u in marg[i].items():
        for x_v, p_x_v in marg[j].items():
          if (x_u, x_v) in joints[(i, j)]:
            p_x_uv = joints[(i, j)][(x_u, x_v)]
            I += p_x_uv * (math.log(p_x_uv, 2) - math.log(p_x_u, 2) - math.log(p_x_v, 2))
      heapq.heappush(pq, (-I, i, j))

  return pq


def findSet(parent, i):

  while i != parent[i]:
    i = parent[i]

  return i

def buildMST(pq, feature_length):
  """
  Builds the MST using the heap generated above.
  It returns the edges that needs to be connected using the highest mutual information
  """

  parent = list(range(feature_length))
  size = [1]*feature_length

  count = 0
  edges = set()
  while count < feature_length-1:
    item = heapq.heappop(pq)
    i = item[1]
    j = item[2]
    seti = findSet(parent, i)
    setj = findSet(parent, j)
    if seti != setj:
      if size[seti] < size[setj]:
        size[setj] += size[seti]
        parent[seti] = setj
      else:
        size[seti] += size[setj]
        parent[setj] = seti
      edges.add((i, j))
      count += 1

  return edges

G2 = None
pos2 = None

def buildVisual(edges, feature_length, labels, fname, title=None):

  """
  Tree built could be visualized.
  This is just for visual perspectives.
  Saves the graph
  """

  global G2
  global pos2

  if type(G2) == type(None):
    G = nx.Graph()
    for i in range(feature_length):
      G.add_node(i)
    pos = nx.spring_layout(G, k=10., scale = 10)
    G2 = G
    pos2 = pos
  else:
    G = G2
    pos = pos2

  nx.draw_networkx_nodes(G, pos, node_size=1000)

  nx.draw_networkx_labels(G, pos,labels,font_size=8)
  nx.draw_networkx_edges(G, pos, edgelist=list(edges))
  if title:
    plt.title(title)
  plt.savefig(fname)
  plt.close()


##############main#####################

labels = {0: "Age",
          1: "Workclass",
          2: "education",
          3: "education-num",
          4: "marital-status",
          5: "occupation",
          6: "relationships",
          7: "race",
          8: "sex",
          9: "capital-gain",
          10: "capital-loss",
          11: "hours-per-week",
          12: "native-country",
          13: "salary",
         }

f = open("data.txt", "r")
joints = {}
marg = {}
gibbs_marg = {}

feature_length = 14
data_size = 25000
test_size = 0

for i in range(feature_length):
  marg[i] = defaultdict(float)
  gibbs_marg[i] = defaultdict(float)
  for j in range(i+1, feature_length):
    joints[(i, j)] = defaultdict(float)

count_aggr = 0

dataset = []
testset = []
literals = [[] for i in range(14)]
#Reading of file
for line in f:
  n = line.strip().split("  ")
  dataset.append(n)
  count_aggr += 1

  #Calculates the marginal and joint distributions of the dataset
  #Each marginal feature has a dictionary telling the probability of getting that value
  #For each of the pair of features what is the probability of getting the two value pair together
  for i in range(feature_length):
    marg[i][n[i]] += 1./data_size
    if(n[i] not in literals[i]):
        literals[i].append(n[i])
    for j in range(i+1, feature_length):
      joints[(i,j)][(n[i], n[j])] += 1./data_size

#Reading end
pq = ProcessPQ(joints, marg, feature_length)
edges = buildMST(pq, feature_length)
buildVisual(edges, feature_length, labels, "final.jpg", title="%d samples"%data_size)
#print(pq)
#print (edges)
f = open("data_test.txt", "r")
for line in f:
    n = line.strip().split("  ")
    testset.append(n)
    test_size += 1
#Consider p is parent of q
#You can use the joint probabilities and marginal probabilities calculated above in your code
#Write your code here
def generateRandomSample():
    result = []
    for i in range(14):
        st = randint(0, len(literals[i]) - 1)
        result.append(literals[i][st])
    return result

def generateTestSample(sample):
    result = []
    st = randint(0, test_size - 1)
    result = testset[sample]
    result[13] = literals[13][randint(0, len(literals[13]) - 1)]
    return result

nearby = [[] for i in range(14)]
parent = [[] for i in range(14)]
child = [[] for i in range(14)]
for i in range(14):
    for j in range(14):
        if((i, j) in edges or (j, i) in edges):
            nearby[i].append(j)
        if((i, j) in edges):
            child[i].append(j)
        if((j, i) in edges):
            parent[i].append(j)

def conditionalProb(index, sample):
    result = literals[index]
    prob = [1] * len(result)
    app = []
    for i in range(data_size):
        flag = 1
        for j in range(len(nearby[index])):
            c = nearby[index][j]
            if(sample[c] != dataset[i][c]):
                flag = 0
                break
        if(flag == 1):
            app.append(dataset[i][index])
    for i in range(len(result)):
        prob[i] = app.count(result[i])
    return prob

def resample(p):
    """curMin = min(p)
    p[:] = [x - curMin for x in p]
    curMax = max(p)
    p[:] = [x / curMax for x in p]"""
    a = []
    for i in range(len(p)):
        a.extend(i for x in range(p[i]))
    resampled = randint(0, len(a) - 1)
    return a[resampled]

iteration = 100
samples = 200
correct = 0.0
wrong = 0.0
gibbset = []
for sample in range(samples):
    s = generateRandomSample()
    for i in range(iteration):
        index = randint(0, 13)
        #print(s)
        #print(index)
        p = conditionalProb(index, s)
        if(all(v == 0 for v in p)):
            continue
        resampled = resample(p)
        #print(resampled)
        s[index] = literals[index][resampled]
        present = 0
    if(s in testset):
        correct += 1
    else:
        temp = s[13]
        for i in literals[13]:
            s[13] = i
            if(s in testset):
                wrong += 1
        s[13] = temp

    gibbset.append(s)
    """print (sample)
    print(correct)
    print(wrong)
    print("-----")"""

print("{0} times iterated".format(iteration))
print("{0} samples generated".format(samples))
print("{0} completely matched with test data".format(correct))
print("{0} gave incorrect population estimate".format(wrong))
if((correct + wrong) != 0):
    print("{0} probability of correct population estimate".format((correct / (correct + wrong))))
absgibbs = []
abstestset = []

for i in range(samples):
    for j in range(feature_length):
      gibbs_marg[j][gibbset[i][j]] += 1./samples
error = 0.0
nf = 0
for i in range(feature_length):
    for j in (marg[i]):
        error += abs(marg[i][j] - gibbs_marg[i][j])
        nf += 1.0
error = error / nf

print("{0} is the marginal absolute error from Gibbs samples".format(error))

for i in range(samples):
    if(gibbset[i] in absgibbs):
        continue
    absgibbs.append(gibbset[i])

for i in range(test_size):
    if(testset[i] in abstestset):
        continue
    abstestset.append(testset[i])

counter = [[] for i in range(len(abstestset))]
testcounter = [[] for i in range(len(abstestset))]

for i in range(len(abstestset)):
    counter[i] = gibbset.count(abstestset[i])

for i in range(len(abstestset)):
    testcounter[i] = testset.count(abstestset[i])

counter = [i / samples for i in counter]
testcounter = [i / test_size for  i in testcounter]
error_per_index = [abs(i) for  i in list(map(operator.sub, testcounter, counter))]
error_occurence = sum(error_per_index) / len(abstestset)
print("{0} error of occurence of likelihood".format(error_occurence))
