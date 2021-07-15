
# proDEX is a probabilistic DEX methodology tool
# written in Python
# (subsumes the special research tools: pyDEXprob and pyDEXnum)
# [Martin Znidarsic]
# + mini adaptation for Python3 compliance

class Node:
    # class of proDEX node
    def __init__(self):
        self.name = None
        self.type = "discrete"    # can be: "discrete", "continuous" or "None" for unknown
        self.values = []    # list of possible values the node can take, or interval [lo, hi] for continuous
        self.ordered = None # can be: "True", "False" or "None" for unknown
        self.parents = []
        self.children = []
        self.tableFunction = []
        self.generalFunction = None  # General function - for parents (disc. or cont.) of continuous only

    def setName(self, name):
        self.name = name

    def setType(self, type):
        self.type = type
                
    def setValues(self, valuesList):
        self.values = valuesList

    def setParent(self, parent):
        self.parents.append(parent)

    def addChild(self, child):
        self.children.append(child)

    def addFunctionRow(self, row):
        # row is formed as [[val1, val2,.., valn], {classDist}, confidence(float)]
        ##check if row is in the right format
        ##check if the row is not already there
        self.tableFunction.append(row)

    def printFunction(self):
        for i in range(len(self.tableFunction)):
            rowString=""
            for j in range(len(self.tableFunction[i])):
                    rowString = rowString + "%s \t" % self.tableFunction[i][j]
            print(rowString)


        
class Atrib:
    # class of DEX attribute
    def __init__(self):
        self.name = None
        self.type = "discrete"    # can be: "discrete", "continuous" or "None" for unknown
        self.values = []    # list of possible values the attribute can take
        self.parents = []
        self.values = []    # list of possible values the node can take, or interval [lo, hi] for continuous
        self.ordered = None # can be: "True", "False" or "None" for unknown        

    def setName(self, name):
        self.name = name
        
    def setType(self, type):
        self.type = type
                        
    def setValues(self, valuesList):
        self.values = valuesList

    def setParent(self, parent):
        self.parents.append(parent)





def getAtribs(somenode):
    # collects all the Atrib-s below a node into a list and returns it
    list = []
    if isinstance(somenode, Node):
        for c in somenode.children:
            for el in getAtribs(c):
                if el not in list:
                    list.append(el)
    elif isinstance(somenode, Atrib):
        list.append(somenode)
    return list


def getNodes(somenode):
    # collects all the Node-s below a node into a list and returns it
    # -- this function was added on 21.9.2004 -- 
    list = []
    if isinstance(somenode, Node):
        list.append(somenode)
        for c in somenode.children:
            for el in getNodes(c):
                if el not in list:
                    list.append(el)
    return list


def getValues(node):
    return node.values


def getAllValues(someone):
    # returns a list of values-lists for all attributes under someone
    atribs = getAtribs(someone)
    listOfValues = []
    for a in atribs:
        listOfValues.append(a.values)
    return listOfValues


def permute(Lists):
    # returns a list of permutations given list of lists
  import operator
  if Lists:
    result = map(lambda I: [I,], Lists[0])
    for list in Lists[1:]:
      curr = []
      for item in list:
        new = map(operator.add, result, [[item,]]*len(result))
        curr[len(curr):] = new
      result = curr
  else:
    result = []
  return result


def getAllVariants(someone):
    valsList = getAllValues(someone)
    valsList.reverse()  # because permute gives them in wrong order
    per = permute(valsList)
    for i in range(len(per)):
        per[i].reverse()    # because permute gives them in TWICE wrong order
    valsList.reverse()
    return per


def printAllVariants(someone):
    variants = getAllVariants(someone)
    for i in range(len(variants)):
        varstring = ""
        for j in range(len(variants[i])):
            varstring = varstring + "%s\t" % variants[i][j]
        print(varstring)


def getSituation(node):
    # situation can be:
    # 1 (discrete parent of discrete children),
    # 2 (discrete parent of a single continuous child - discretization)
    # or 3 (continuous parent of continuous children)
    if node.type=="discrete":
        if len(node.children)==1:   # single child
            if node.children[0].type=="discrete":
                return 1
            elif node.children[0].type=="continuous":
                return 2
        else:   # multiple children
            for c in node.children:
                if c.type=="continuous":
                    print("Error: cont. children of disc. parent!")
                    return None
            return 1
    elif node.type=="continuous":
        if len(node.children)==1:   # single child
            if node.children[0].type=="discrete":
                print("Error: cont. parent has a discrete child!")
                return None
            elif node.children[0].type=="continuous":
                return 3
        else:   # multiple children
            for c in node.children:
                if c.type=="discrete":
                    print("Error: disc. children of cont. parent!")
                    return None
            return 3



def classify(variant, root):
    # returnes the class of variant given the root of the model
    returnValue = None
    if isinstance(root, Atrib): # stopping criterion
        if root in variant.keys():
            returnValue = variant[root]
        else:
            print("Error: attribute not in the variant dictionary!")
            print("Attribute's name: ", root.name)
    else:
        computedVariant={}
        for c in root.children:
            if c.type == "continuous" and isinstance(c, Atrib):  # only one continuous
                returnValue = root.generalFunction(variant[c])   #discretize child
            elif c.type == "continuous" and isinstance(c, Node):    # top of cont. tree
                print("CLASSIFICATION FOR CONT. SUBTREES IS NOT MADE YET!")
                returnValue = root.generalFunction(classify(variant,c)) #make classif. for continuous!
            else:
                if c in variant.keys(): # if child value (dist.) already given, do not calculate.
                    computedVariant[c] = variant[c]
                else:
                    computedVariant[c] = classify(variant, c)
                # this way all the children values get to computedVariant dictionary
        if returnValue == None: # so, if not continuous..
            # now classify according to tableFunction:
            if type(root.tableFunction[0][1]) == str:   #crisp rules - preverjem kar naivno na podlagi prvega pravila
                for rule in root.tableFunction:
                    combinationDict = rule[0]
                    match = True
                    for k in combinationDict.keys():
                        if combinationDict[k] != computedVariant[k]:
                            match = False
                    if match == True:
                        returnValue = rule[1]
            else: #probabilistic rules
                conFlag = False
                resultDict={}
                for v in root.values:
                    resultDict[v]=0.0
                resultDict["CONFIDENCE"] = 0.0
                for rule in root.tableFunction:
                    combinationDict = rule[0]
                    distributionDict = rule[1]
                    if "CONFIDENCE" in distributionDict.keys():
                        conFlag = True
                    f = 1 #factor - probability of rule
                    childrenConfidence = 1.0
                    for child in root.children:
                        ruleValue = combinationDict[child]  # string: value of a certain child in the rule
                        thisChildsDistribution = computedVariant[child]
                        if f != 0.0:  # if f=0.0, it has no sense to calculate further 
                            f = f * thisChildsDistribution[ruleValue]
                        if ("CONFIDENCE" in thisChildsDistribution.keys()) and (thisChildsDistribution["CONFIDENCE"]!=None):
                            childrenConfidence = childrenConfidence * thisChildsDistribution["CONFIDENCE"]
                    for k in resultDict.keys():
                        if k=="CONFIDENCE":
                            if "CONFIDENCE" in distributionDict.keys():
                                #print "Pred mnozenjem je childrenConfidence: ", childrenConfidence
                                if f != 0.0:    # if f=0.0, it has no sense to calculate further 
                                    resultDict[k] = resultDict[k] + (f * childrenConfidence * distributionDict["CONFIDENCE"])
                        else:
                            if f != 0.0:    # if f=0.0, it has no sense to calculate further 
                                resultDict[k] = resultDict[k] + (f * distributionDict[k])
                if conFlag == False:
                    resultDict["CONFIDENCE"] = None
                returnValue = resultDict
    return returnValue



def getAttributeNumber(somenode):
    # returns the number of attributes 'somenode' covers
    returnValue = None
    if isinstance(somenode, Atrib):
        returnValue = 1
    elif isinstance (somenode, Node):
        sum = 0
        for c in somenode.children:
            sum = sum + getAttributeNumber(c)
        returnValue = sum
    else: print("Exception: getAttributeNumber called with unknown object")
    return returnValue
    
        

def getAllVariantsWithClass(someone):
    # gives "data from the model" in a variantClass list
    variants = getAllVariants(someone)
    for i in range(len(variants)):
        classValue = classify(variants[i], someone)
        variants[i].append(classValue)
    return variants


def printAllVariantsWithClass(modelRoot):
    # produces "data from the model" in tab delimited format
    variants = getAllVariants(modelRoot)
    for i in range(len(variants)):
        varstring = ""
        classValue = classify(variants[i], modelRoot)
        for j in range(len(variants[i])):
            varstring = varstring + "%s\t" % variants[i][j]
        varstring = varstring + str(classValue)
        print(varstring)

# it is hard to test how valid is the classification result
# since the result is a distribution and not a crisp value
# possibility : difference in distribution (sum of real diff. at each value - then relative?)
def classifyDataFile(filename, modelRoot):
    # classifies data from given file with given model and provides CA
    dataFile = open(filename, 'r')
    entriesNumber = 0   #counts the rows
    difSum = 0  #overall differential sum
    row = dataFile.readline()
    while row:
        cvariant = []
        el = ''
        for i in range(len(row)):
            if row[i]=='\t': cvariant.append(el); el=''
            ###elif row[i]==' ': cvariant.append(el)
            elif row[i]=='\n': cvariant.append(el)
            else : el = el + row[i]
        variant = cvariant[:-1] # we strip the class off
        cstring = cvariant[-1:][0]
        classValue = eval(cstring)   #we save the class value
        print(type(classValue))
        resultValue = classify(variant, modelRoot)
        entriesNumber = entriesNumber + 1
        for k in (eval(classValue)).keys():
            difSum = difSum + abs((eval(classValue))[k] - resultValue[k])
        row = dataFile.readline()
    dataFile.close()
    relativedifSum = float(difSum) / entriesNumber
    return 1-relativedifSum


def classifyCrispDataFile(filename, modelRoot):
    # classifies data from given file with given model and provides CA
    dataFile = open(filename, 'r')
    entriesNumber = 0   #counts the rows
    difSum = 0  #overall differential sum
    row = dataFile.readline()
    while row:
        cvariant = []
        el = ''
        for i in range(len(row)):
            if row[i]=='\t': cvariant.append(el); el=''
            ###elif row[i]==' ': cvariant.append(el)
            elif row[i]=='\n': cvariant.append(el)
            else : el = el + row[i]
        variant = cvariant[:-1] # we strip the class off
        cstring = cvariant[-1:][0] # class
        resultValue = classify(variant, modelRoot)
        entriesNumber = entriesNumber + 1
        difSum = difSum + abs(1 - resultValue[cstring])
        row = dataFile.readline()
    dataFile.close()
    relativedifSum = float(difSum) / entriesNumber
    return 1-relativedifSum


# with PROB we do not need monotonicity check
##def monOKhandy(someone, clashingVariant2):

##def monOK(someone, clashingVariant2):


def distDiff(d1, d2):
    # distribution difference among distributions d1 and d2
    diff = 0
    for k in d1.keys():
        diff = diff + abs(d1[k] - d2[k])
    return diff


def maxKey(di):
    max = 0
    maxkey = None
    for k in di.keys():
        if di[k] > max:
            max = di[k]
            maxkey = k
    return maxkey


# Node changing part - for automatic update
def changeNode(node, newVariant):
    # changes the right variant in 'node' to 'newVariant'
    # newVariant CANNOT be flat
    if len(node.tableFunction[0]) == len(newVariant):
        # then find the right row and change it
        print(len(node.tableFunction))
        for f in node.tableFunction:
            if f[:-1] == newVariant[:-1]:
                #f = newVariant ###doesn't work
                node.tableFunction.remove(f)
                node.tableFunction.append(newVariant)




def updateFromFile(modelRoot, newDataFile, trust=0.1):
    # updates the old model (given with "modelRoot")
    # according to new data (given with "newDataFile" tabulated file)
    # Procedure changes old model !!! Only in RAM of course :)
    # As a result it prints all table functions of the new model
    dataFile = open(newDataFile, 'r')
    row = dataFile.readline()
    while row:
        # <-parsing->
        cvariant = []
        el = ''
        for i in range(len(row)):
            if row[i]=='\t': cvariant.append(el); el=''
            elif row[i]=='\n': cvariant.append(el)
            else : el = el + row[i]
        # cvariant now contains the variant+class from current row in new data file
        # <-parsing->
        clist=[]
        update(modelRoot, modelRoot, cvariant, clist, trust, dFile=newDataFile)
        row = dataFile.readline()
    dataFile.close()
    print("New table functions are:")
    print(modelRoot.name, " :")
    for t in range(len(modelRoot.tableFunction)):
        print(modelRoot.tableFunction[t])
    print
    for i in range(len(modelRoot.children)):
        print (modelRoot.children[i]).name
        for j in range(len((modelRoot.children[i]).tableFunction)):
            print (modelRoot.children[i]).tableFunction[j]
        print
    print("UPDATE FINISHED.")


def update(modelRoot, node, newVariant, changesList, trust=0.1, dFile=None):
    # updates the node (step 1) and children (step 2)
    # newVariant can be flat or not
    # <--getting the goal distribution-->
    distC = classify(newVariant[:-1], node)
    actualClass = newVariant[-1:][0]
    goalDist = {}
    for k in distC.keys():
        if k == actualClass:
            goalDist[k] = float(distC[k] + trust) / (1+trust)
        else:
            goalDist[k] = float(distC[k]) / (1+trust)
    # <--getting the goal distribution-->

    
    # <finding node children to amplify>
    m = max(map(len,map(getValues, node.children))) #max ValuesCount in children
    # we seek m most similar distributions

    closestChildrenVals = []
    for f in node.tableFunction:
        closestChildrenVals.append((distDiff(f[-1:][0], goalDist), f[:-1])) #only children f[:-1]
    closestChildrenVals.sort()
    closestChildrenVals = closestChildrenVals[:m]   #we pick only the closest m

    # closestChildrenVals = [(distDiff1, [v1,v2]), (distDiff2, [v1',v2']), (distDiff3, [v1'',v2''])]
    # - before it was only = [val1, val2]
    # <--finding node children to amplify-->

    
    if len(node.tableFunction[0]) == len(newVariant):
        #variant matches the node
        #<--step 1-->
        for f in node.tableFunction:
            if f[:-1] == newVariant[:-1]:   #all but class matches
                rowBefore = f[:] #copy list contents
                rowBefore[-1:][0] = {}
                dicti = f[-1]
                rowBefore[-1] = dicti.copy()
                print(rowBefore)
                oldDict = f[-1]    #old class dist. dictionary
                for k in oldDict.keys():
                    if k == newVariant[-1:][0]: #class name matches with one from data
                        oldDict[k] = float(oldDict[k] + trust) / (1+trust)
                    else:
                        oldDict[k] = float(oldDict[k]) / (1+trust)
                rowAfter = f[:]
                rowAfter[-1:][0] = {}
                dicti2 = f[-1]
                rowAfter[-1] = dicti2.copy()
                if node.name != modelRoot.name:
                    changesList.append( (node.name, rowBefore, rowAfter) ) 
        #<--step 1-->
        #<--step 2-->
        # in this case there must be only atribs as children..no step 2
        for child in node.children:
            if isinstance(child, Node): print("CAUTION child node skipped!")
        #<--step 2-->
    else:
        #variant is flat for the node
        # then we have to evaluate children first
        childValues = []
        childAtribs = []
        for c in node.children:
            atNum = getAttributeNumber(c)
            childDist = classify(newVariant[:atNum], c)
            childValues.append(maxKey(childDist))   #we append the most probable value
            childAtribs.append(newVariant[:atNum])
            newVariant = newVariant[atNum:]
        #<--step 1-->
        for f in node.tableFunction:
            if f[:-1] == childValues:   #all but class matches
                rowBefore = f[:] #copy list contents
                rowBefore[-1:][0] = {}
                dicti = f[-1]
                rowBefore[-1] = dicti.copy()
                oldDict = f[-1]    #old class dist. dictionary
                for k in oldDict.keys():
                    if k == newVariant[-1:][0]: #class name matches with one from data
                        oldDict[k] = float(oldDict[k] + trust) / (1+trust)
                    else:
                        oldDict[k] = float(oldDict[k]) / (1+trust)
                rowAfter = f[:]
                rowAfter[-1:][0] = {}
                dicti2 = f[-1]
                rowAfter[-1] = dicti2.copy()
                if node.name != modelRoot.name:
                    changesList.append( (node.name, rowBefore, rowAfter) ) 
                
        #<--step 1-->
        #<--step 2-->

        # FOR NOW - we promote all m similar ones
        # closestChildrenVals = [(distDiff1, [v1,v2]), (distDiff2, [v1',v2']), (distDiff3, [v1'',v2''])]
        # - before it was only = [val1, val2]
        bestCA = classifyCrispDataFile(dFile, modelRoot)
        bestCCV = None
        for j in range(len(closestChildrenVals)):
            ccv = closestChildrenVals[j][1] #one variant to promote
            childrenChangesList = []
            for i in range(len(ccv)):
##            if neighbors(closestChildrenVals[i], childValues[i], node, i):
                # we merge atribs and class(to be emphasized)
                # NOW WE NEED CHANGE/UNCHANGE PROCEDURE..
                # A NEW UPDATE THAT TRACKS CHANGES!! different from normal update, because
                # this one must not track the change of action 1 and thus is not general enough.
                # although we could say if node = rootnode do not track...YES - Solution!
                # we need the root node as input anyway now.. 
                childVariant = childAtribs[i] + [ccv[i]]
                thisOne=[]
                update(modelRoot, node.children[i], childVariant, thisOne, trust, dFile)
                childrenChangesList = childrenChangesList + thisOne                
            ca = classifyCrispDataFile(dFile, modelRoot)
            if ca > bestCA:
                bestCCV = ccv
                bestCA = ca
            unchange(node, childrenChangesList)
        # now make only the best promotion
        if bestCCV != None:
            for ind in range(len(bestCCV)):
                childVariant = childAtribs[ind] + [bestCCV[ind]]
                thisOne = []
                update(modelRoot, node.children[ind], childVariant, thisOne, trust, dFile)
            changesList = changesList + thisOne
        #<--step 2-->
    if node.name == modelRoot.name:
        print("since I am root (%s), here are the changes of updating below me:" % node.name)
        for c in changesList:
            print(c)



def unchange(node, changesList):
    for c in node.children:
        for el in changesList:
            if c.name == el[0]: #name matches nodename
                for i in range(len(c.tableFunction)):
                    if c.tableFunction[i] == el[2]:    #row matches rowAfter
                        c.tableFunction[i] = el[1]     #then make it as before
                changesList.remove(el)





def neighbors(val1, val2, node, i):
    result = None
    child = node.children[i]
    for a in range(len(child.values)):
        if child.values[a] == val1:
            index1 = a
        if child.values[a] == val2:
            index2 = a
    if abs(index1 - index2) < 2:
        result = 1
    return result



#### HISTORY ######

def readXMLmodel(fname):
    #reads a model from a DEX model file in PMML format and returns the models top node
    from xml.dom import minidom
    modelDict = {}  # dictionary that holds the variables (Nodes and Atribs)
    xmldata = minidom.parse(fname)
    model = xmldata.childNodes[1]
    hierarchy = model.childNodes[2]
    miningschema = hierarchy.childNodes[0]
    #now we find out which are Nodes and which Atribs..and create them
    for el in miningschema.childNodes:
        elname = str(el.attributes.get('name').value)
        elusage = el.attributes.get('usageType').value
        if elusage=='predicted':
            modelDict[elname] = Node()
            modelDict[elname].setName(elname)
        elif elusage=='active':
            modelDict[elname] = Atrib()
            modelDict[elname].setName(elname)
        else : print("ERROR - unusual type of attribute in miningschema.")
    #then we find relations among them and connect them accordingly
    att = hierarchy.childNodes[1]
    topNodeName = att.attributes.get('name').value
    recurSetRelations(att, modelDict)
    # -- works fine -- the structure of the model is built!
    #now to the values..
    datadictionary = model.childNodes[1]
    for datafield in datadictionary.childNodes:
        dfName = datafield.attributes.get("name").value
        valuesList = []
        for item in datafield.childNodes:
            if item.localName == 'Value':   # we ignore 'Extension'-s
                valuesList.append(str(item.attributes.get("value").value))  #works only for 'u strings so far
        valuesList.reverse()
        modelDict[dfName].values = valuesList
    #now to the rule-based functions..
    functionlist = hierarchy.childNodes[2]
    for function in functionlist.childNodes:
        # 'function' is a function of one Node
        fuName = function.attributes.get("name").value  #fuName is the name of the Node with this function
        print("parsing node: %s" % str(fuName))
        for rule in function.childNodes:
            # 'rule' is one rule in the 'function'
            ruleDict={} #dict. of subnodes values (the first element of function row)
            condition = rule.childNodes[0]
            result = rule.childNodes[1]
            compoundpredicate = condition.childNodes[0]
            if compoundpredicate.attributes.get("booleanOperator").value != "and": print("ERR: compound predicate in XML is not AND!")
            childNum = len(modelDict[fuName].children)
            for i in range(childNum):
                try:
                    if compoundpredicate.childNodes[i].attributes.get("field").value == modelDict[fuName].children[i].name:
                        ruleDict[modelDict[fuName].children[i]]= str(compoundpredicate.childNodes[i].attributes.get("value").value)
                    else:
                        print("ERR: wrong child order in XML file!")
                        print(compoundpredicate.childNodes[i].attributes.get("field").value , " is not equal to " , modelDict[fuName].children[i].name)
                except IndexError:
                    print("OOPS! Children index problem.")
                    print("The problematic Node is : ", fuName)
            # now we add the last item in the list that represents the rule:
            valueDict={} #dict. of Node values (actually a prob. distribution)
            for val in modelDict[fuName].values:
                if val == str(result.childNodes[0].attributes.get("value").value):
                    valueDict[val] = 1.0
                else:
                    valueDict[val] = 0.0
            # and add this to the utility function:
            modelDict[fuName].addFunctionRow([ruleDict, valueDict])
    return modelDict[topNodeName]


def recurSetRelations(it, modelDict):
    for c in it.childNodes:
        modelDict[it.attributes.get('name').value].addChild( modelDict[c.attributes.get('name').value] )
        modelDict[c.attributes.get('name').value].setParent( modelDict[it.attributes.get('name').value] )
        if isinstance(modelDict[c.attributes.get('name').value], Node):
            recurSetRelations(c, modelDict)
        

def revision(modelRoot, node, newVariant, changesList, cN=0.5, trust=0.1, dFile=None):
    if isinstance(node, Atrib): return  # stopping criterion
    # revises the node with respect to CONFIDENCE ###(step 1) and children (step 2)
    # <--getting the goal distribution for step 1-->
    actualClass = newVariant[node.name]
    print("actualClass is:", actualClass)
    # get childer evaluations and get the most probable combination of values
    mpCombDict = {} # {c1:[val1], c2:[val2.1,val2.2],.., cN:[valN]} most probable combination of children values given newVariant attributes
    childrenNVresults = {}  # a dict. of children classification results for use later in 2.step
    for c in node.children:
        cdis = classify(newVariant, c)
        print("cdis of " +str(c.name) + " " + str(cdis))
        childrenNVresults[c]=cdis   # saving this for later use in 2.step
        maxP = -1.0
        mpCombDict[c]=[]
        for k in c.values:  # must be in c.values to avoid CONFIDENCE
            if cdis[k] > maxP:
                maxP = cdis[k]
        if (maxP == -1.0):
            print("ERROR in revision: no max childProb value!")
        else:
            for k in c.values:
                if cdis[k] == maxP:
                    (mpCombDict[c]).append(k) # append the maxValue to the list of this child
    ##print "ETO: maxProb je " + str(maxP) + " dosezejo jo pa tile: "; print mpCombDict
    print("Revision will be made with cN=" + str(cN))
    # <--make step 1-->
    for rule in node.tableFunction:
        combinationDict = rule[0]
        rightRule = True   # only if all the values are the same, it is true
        for k in combinationDict.keys():
            if combinationDict[k] not in mpCombDict[k]:
                rightRule = False
        if rightRule == True:   # do the revision step 1 on this one (should happen once in a table function)
            for key in (rule[1]).keys():
                if (key != "CONFIDENCE") and (key == actualClass):
                    (rule[1])[key] = ((rule[1])[key] * (rule[1])["CONFIDENCE"] * (1-cN) + 1 * cN * (1 - (rule[1])["CONFIDENCE"])) / ((rule[1])["CONFIDENCE"] * (1-cN) + cN * (1 - (rule[1])["CONFIDENCE"]))
                elif (key != "CONFIDENCE") and (key != actualClass):
                    (rule[1])[key] = ((rule[1])[key] * (rule[1])["CONFIDENCE"] * (1-cN))  / ((rule[1])["CONFIDENCE"] * (1-cN) + cN * (1 - (rule[1])["CONFIDENCE"]))
            (rule[1])["CONFIDENCE"] = ((rule[1])["CONFIDENCE"] * (1-cN) + cN * (1 - (rule[1])["CONFIDENCE"])) / ((rule[1])["CONFIDENCE"] * (1-cN) + cN * (1 - (rule[1])["CONFIDENCE"]) + (1 - (rule[1])["CONFIDENCE"]) * (1-cN) )
            print
            print("REVISION MADE!")
            print("--on node: " + str(node.name) + " forcing " + str(actualClass) + " into row " + str(rule[0]))
##            print "--new dist.: " + str(rule[1])
##            print "--new CONFIDENCE: " + str((rule[1])["CONFIDENCE"])
##            print
    # <--end step 1, make step 2-->
    # zdaj najdi kombinacijo ki v node.tableFunction najbolj zadene pravi class, dodaj to v newVariant in rekurzivno poklici revizijo
    highestProb = -1.0
    ## highestCombination = None    - ne rabim vec, saj delam seznam
    for rule in node.tableFunction:
        distDict = rule[1]
        if distDict[actualClass] > highestProb:
            highestProb = distDict[actualClass]
            ## highestCombination = rule[0] - ne rabim vec, saj delam seznam
    # se en sprehod skozi da poberemo morebitne kombinacije ki so vse "highestProb"
    highestCombinationList = []
    for rule in node.tableFunction:
        distDict = rule[1]
        if distDict[actualClass] == highestProb:
            highestCombinationList.append(rule[0])
    print("Number of equaly high for " + str(node.name) + " is: " + str(len(highestCombinationList)))
    # naslednji korak je izbira najmanj divergiranega od teh..
    # childrenNVresults = {child1:{"val1":#1, "val2":#2, CONFIDENCE:#3}, .., childN:{...}}
    maxWeight = -1.0
    for hcomb in highestCombinationList:
        weight = None
        for kx in hcomb.keys():
            actualValue = hcomb[kx] # actualValue is like "low"
            kxDict = childrenNVresults[kx]
            if weight == None:  # first call
                weight = kxDict[actualValue]
            else:
                weight = weight * kxDict[actualValue]
        if weight > maxWeight:
            maxWeight = weight
    # now we have the maximum weight of all the combinations
    # another for-clause to pick all combinations (maybe more than one) with such a weight
    for hcomb in highestCombinationList:
        weight = None
        for kx in hcomb.keys():
            actualValue = hcomb[kx] # actualValue is like "low"
            kxDict = childrenNVresults[kx]
            if weight == None:  # first call
                weight = kxDict[actualValue]
            else:
                weight = weight * kxDict[actualValue]
        if weight == maxWeight:
            print("Of equal, this one:" + str(hcomb) + " has the highest weight of " + str(weight) + ".")
            for key in hcomb.keys():
                newVariant[key.name] = hcomb[key]
                print("calling children revision on " + str(key.name) + " with newvariant:"+str(newVariant))
                revision(modelRoot, key, newVariant, changesList, cN, trust=0.1, dFile=None)
    # <--end step 2-->            


def revisionFromFileBatch(modelRoot, newDataFile, cN=0.5, trust=0.1, quiet=False):
    # updates the old model (given with "modelRoot")
    # according to new data (given with "newDataFile" tabulated file) in a BATCH mode
    # Procedure changes old model !!! Only in RAM of course :)
    # As a result it prints all table functions of the new model
    import copy #because we need the deepcopy function
    import orange   #because the new data are read as orange.ExampleTable (from file in Orange tab. format)
    # <-begin--save the original table functions->
    originalDict={}
    nodes = getNodes(modelRoot)
    for n in nodes:
        originalDict[n.name]=n.tableFunction
    safeOriginalCopy = copy.deepcopy(originalDict)
    # <-end--save the original table functions->
    if quiet==False: print("original functions:"); print(safeOriginalCopy)
    # <-begin--make initial empty dict of differences->
    differences = {}    #the initially empty (all zeros in distributions) table function dictionary
    differences = copy.deepcopy(originalDict)
    for k in differences.keys():
        tf = differences[k]
        for interList in tf:
            interDic = interList[-1:][0]
            for kk in interDic.keys():
                interDic[kk]=0.0
    # <-end--make initial empty dict of differences->
    if quiet==False: print("initial (empty) diferences:"); print(differences)
    # --------tukaj pa naredi zdaj branje s pomocjo Orange.ExampleTable:
    data = orange.ExampleTable(newDataFile)
    atribs = getAtribs(modelRoot)  # a more general revision would check also for Nodes..
    for i in range(len(data)):
        # <-reading->
        newVariant = {}
        for atrib in atribs:
            newVariant[atrib] = {}
            for val in atrib.values:
                if val == data[i][atrib.name].value:
                    (newVariant[atrib])[val] = 1.0
                else:
                    (newVariant[atrib])[val] = 0.0
        newVariant[modelRoot.name] = data[i].getclass().value
        print("--/\--")
        print("Calling revision with: ")
        print(newVariant)
        print("--/\--")
        # <-reading->
        revision(modelRoot, modelRoot, newVariant, [], cN)
        # -- now we have to put this into differences and reset the model
        # -- all but the CONFIDENCE get added and normalized
        #<-begin--add to differences - NORMALIZATION!>
        for k in originalDict.keys():
            tf = originalDict[k]
            difftf = differences[k]
            stf = safeOriginalCopy[k]
            for interList in tf:    # spremembe naj se dodajo samo ce so bile dejansko narejene (preveris z == safeOriginalCopy)
                interDic = interList[-1:][0]
                diffinterList = difftf[tf.index(interList)]
                diffinterDic = diffinterList[-1:][0]
                stfinterList = stf[tf.index(interList)]
                stfinterDic = stfinterList[-1:][0]
                # -- dodano 28.11.2005
                changeMade = False
                for kk in interDic.keys():
                    if kk != 'CONFIDENCE':
                        if interDic[kk] != stfinterDic[kk]:
                            changeMade = True
                # --
                if changeMade == True:
                    sumProbabs = 0.0
                    for kk in interDic.keys():
                        if kk != 'CONFIDENCE':
                            diffinterDic[kk] = diffinterDic[kk] + interDic[kk]
                            sumProbabs = sumProbabs + diffinterDic[kk]
                        else:
                            if interDic[kk] != 0.6: #ATTENTION - datset specific!
                                print("interDic kaze na spremembo CONF iz 0.6")
                                print
                                diffinterDic[kk] = diffinterDic[kk] + 1 #for CONFIDENCE : just adding the number of applications
                    for kk in diffinterDic.keys(): #normalization
                        if kk != 'CONFIDENCE':
                            diffinterDic[kk] = diffinterDic[kk] / float(sumProbabs)
        #<-end--add to differences>
        print("DIFFERENCES:")
        print(differences)
        print
##        if quiet==False:
##            print "----------------------------------------"
##            print "BEFORE reset model gives MAE of", classifyRealDataFile(newDataFile, modelRoot)
        #<-begin--reset the table functions of the model>
        for k in originalDict.keys():
            tf = originalDict[k]
            savedtf = safeOriginalCopy[k]
            for interList in tf:
                interDic = interList[-1:][0]
                savedinterList = savedtf[tf.index(interList)]
                savedinterDic = savedinterList[-1:][0]
                for kk in interDic.keys():
                    if kk != 'CONFIDENCE':  # changed CONFIDENCE stays the same
                        interDic[kk]=savedinterDic[kk]
                    else:
                        interDic[kk]=savedinterDic[kk]  # no, not even CONFIDENCE stays the same!                        
        #<-end--reset the table functions of the model>
##        if quiet==False:
##            print "AFTER reset model gives MAE of", classifyRealDataFile(newDataFile, modelRoot)
##            print "----------------------------------------"
    # \/\/\//\/\/\/\/\/\/\/\/\/\/\/\\/\/\/\/\/\/\/\/\\/\/\/\/\/\/\\/\\\/\/\/\\/\//\/                    
    # -- now we have to add the differences to the model
    #<-begin--add differences to the model - NORMALIZATION>
    for k in originalDict.keys():
        tf = originalDict[k]
        difftf = differences[k]
        for interList in tf:
            interDic = interList[-1:][0]
            diffinterList = difftf[tf.index(interList)]
            diffinterDic = diffinterList[-1:][0]
            sumProbabs = 0.0
            numberOfRevisions = 0
            for kk in interDic.keys():
                if kk != 'CONFIDENCE':
                    interDic[kk] = interDic[kk] + diffinterDic[kk]
                    sumProbabs = sumProbabs + interDic[kk]
                else:
                    numberOfRevisions = int(numberOfRevisions + diffinterDic[kk])
            for kk in interDic.keys(): #normalization
                if kk != 'CONFIDENCE':
                    interDic[kk] = interDic[kk] / float(sumProbabs)
                else: #CONFIDENCE change
                    for n in range(numberOfRevisions):
                        interDic[kk] = (interDic[kk] * (1-cN) + cN * (1 - interDic[kk])) / (interDic[kk] * (1-cN) + cN * (1 - interDic[kk]) + (1 - interDic[kk]) * (1-cN) )
    #<-end--add differences to the model>
    print("New table functions are:")
    print(modelRoot.name, " :")
    for t in range(len(modelRoot.tableFunction)):
        childrenCombinationDict = modelRoot.tableFunction[t][0]
        probDistDict = modelRoot.tableFunction[t][1]
        outString = "" 
        for k in childrenCombinationDict.keys():
            outString = outString + " " + childrenCombinationDict[k] + " "
        ##print outString + "\t\t" + str(probDistDict)
        print('%-20s ==> %s' % (outString, str(probDistDict)))
    print
    for i in range(len(modelRoot.children)):       
        print((modelRoot.children[i]).name)
        for j in range(len((modelRoot.children[i]).tableFunction)):
            childrenCombinationDict = (modelRoot.children[i]).tableFunction[j][0]
            probDistDict = (modelRoot.children[i]).tableFunction[j][1]
            outString = "" 
            for k in childrenCombinationDict.keys():
                outString = outString + " " + childrenCombinationDict[k] + " "
            ##print outString + "\t\t" + str(probDistDict)
            print('%-20s ==> %s' % (outString, str(probDistDict)))
        print
    print("UPDATE FINISHED.")
##    print "And new MAE is: ", classifyRealDataFile(newDataFile, modelRoot)


def revisionFromFile(modelRoot, newDataFile, cN=0.5, trust=0.1, quiet=False):
    # updates the old model (given with "modelRoot")
    # according to new data (given with "newDataFile" tabulated file) in SEQUENTIAL mode
    # Procedure changes old model !!! Only in RAM of course :)
    # As a result it prints all table functions of the new model
    import orange   #because the new data are read as orange.ExampleTable (from file in Orange tab. format)
    data = orange.ExampleTable(newDataFile)
    atribs = getAtribs(modelRoot)  # a more general revision would check also for Nodes..
    for i in range(len(data)):
        # <-reading->
        newVariant = {}
        for atrib in atribs:
            newVariant[atrib] = {}
            for val in atrib.values:
                if val == data[i][atrib.name].value:
                    (newVariant[atrib])[val] = 1.0
                else:
                    (newVariant[atrib])[val] = 0.0
        newVariant[modelRoot.name] = data[i].getclass().value
        # <-reading->
        revision(modelRoot, modelRoot, newVariant, [], cN)
    print("New table functions are:")
    print(modelRoot.name, " :")
    for t in range(len(modelRoot.tableFunction)):
        print(modelRoot.tableFunction[t])
    print
    for i in range(len(modelRoot.children)):
        print((modelRoot.children[i]).name)
        for j in range(len((modelRoot.children[i]).tableFunction)):
            print((modelRoot.children[i]).tableFunction[j])
        print
    print("SEQUENTIAL FILE REVISION FINISHED.")

