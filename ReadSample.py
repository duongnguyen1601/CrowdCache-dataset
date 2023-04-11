#Example of how to read in the data set

import json
import pandas
import numpy
import os

#Read in the full dataset from output.json
outputFile = 'output/output.json'
f = open(outputFile)
dataJson = json.load(f)
f.close()

data = []

for itr in dataJson:
    iteration = {}
    iteration['users'] = pandas.read_json(itr['users'],orient="split")
    iteration['com_graph'] = numpy.array(itr['com_graph'])
    data.append(iteration)

#Access users or communication graph from iteration 0
print(data[0]['users'])
print(data[0]['com_graph'])


#Read in a specific iterations files
iterationFolder = 'output/1'

com_graph_path = os.path.join(iterationFolder,'com_graph.csv')
users_path = os.path.join(iterationFolder,'users.csv')

com_graph = numpy.loadtxt(com_graph_path, delimiter=",")
users = pandas.read_csv(users_path)

print(com_graph)
print(users)
