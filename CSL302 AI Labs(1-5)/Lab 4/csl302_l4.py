import fileinput
import re
import sys
import queue
import time
from collections import deque
def join_list(l):
    return ", ".join([str(s) for s in l])

def findClause(state, clause):
    for i in state:
        if compareClause(i, clause):
            return i
    return None

def compareClause(ground1, ground2):
    if ground1.predicate != ground2.predicate:
        return False
    if len(ground1.params) != len(ground2.params):
        return False
    for i, j in zip(ground1.params, ground2.params):
        if i != j:
            return False
    return True

def compareTruth(ground1, ground2):
    return ground1.truth == ground2.truth and compareClause(ground1, ground2)

class World:
    def __init__(self):
        self.state = dict()
        self.goals = set()
        self.known_literals = set()
        self.actions = dict()

    def doesContain(self, predicate, literals):
        if predicate not in self.state:
            return False
        return literals in self.state[predicate]

    def addClause(self, predicate, literals):
        if predicate not in self.state:
            self.state[predicate] = set()
        self.state[predicate].add(literals)

    def removeClause(self, predicate, literals):
        if predicate in self.state:
            self.state[predicate].remove(literals)

    def addGoal(self, predicate, literals, truth=True):
        g = Clause(predicate, literals, truth)
        self.goals.add(g)

    def addLiteral(self, literal):
        self.known_literals.add(literal)

    def addAction(self, action):
        if action.name not in self.actions:
            self.actions[action.name] = action

    def goalReached(self):
        for g in self.goals:
            if not g.inCurState(self):
                return False
        return True

class Clause:
    def __init__(self, predicate, params, truth=True):
        self.predicate = predicate
        self.params = params
        self.truth = truth

    def getActualParams(self, variables):
        actualParams = list()
        for p in self.params:
            if p in variables:
                actualParams.append(variables[p])
            else:
                actualParams.append(p)
        return Clause(self.predicate, tuple(actualParams), self.truth)

    def inCurState(self, world):
        return world.doesContain(self.predicate, self.params) == self.truth

    def __str__(self):
        name = self.predicate
        if not self.truth:
            name = "!" + name
        return "{0}({1})".format(name, join_list(self.params))

class Action:
    def __init__(self, name, params, pre, post):
        self.name = name
        self.params = params
        self.pre = pre
        self.post = post
        self.complete_post = list(post)
        for p in pre:
            if (findClause(self.complete_post, p) == None):
                self.complete_post.append(p)

    def simple_str(self):
        return "{0}({1})".format(self.name, join_list(self.params))

    def allPossActions(self, world):
        self.allActions = []
        cur_literals = []
        self.generateAllActions(world.known_literals, cur_literals, self.allActions)

    def generateAllActions(self, all_literals, cur_literals, allAct):
        if len(cur_literals) == len(self.params):
            if(not self.validParams(cur_literals)):
                return
            crossParams = dict(zip(self.params, cur_literals))
            actualPre = [i.getActualParams(crossParams) for i in self.pre]
            actualPost = [i.getActualParams(crossParams) for i in self.post]
            allAct.append(Action(self.name, cur_literals, actualPre, actualPost))
            return
        for literal in all_literals:
            if literal not in cur_literals:
                self.generateAllActions(all_literals, cur_literals + [literal], allAct)

    def validParams(self, cur_literals):
        if(self.name == "Go" and not(cur_literals[0][0] == 'r' and cur_literals[1][0] == 'r')):
            return False
        if(self.name == "Push" and not(cur_literals[0][0] == 'b' and cur_literals[1][0] == 'r' and cur_literals[2][0] == 'r')):
            return False
        if(self.name == "Climbup" and not(cur_literals[0][0] == 'b' and cur_literals[1][0] == 'r')):
            return False
        if(self.name == "Climbdown" and not(cur_literals[0][0] == 'b')):
            return False
        if(self.name == "Turnon" and not(cur_literals[0][0] == 'r' and cur_literals[1][0] == 'b')):
            return False
        if(self.name == "Turnoff" and not(cur_literals[0][0] == 'r' and cur_literals[1][0] == 'b')):
            return False
        return True

    def __str__(self):
        return "{0}({1})\nPre: {2}\nPost: {3}".format(self.name, join_list(self.params), join_list(self.pre), join_list(self.post))

planner = None
def createWorld():
    w = World()
    filename = sys.argv[1]
    predicateRegex = re.compile('(!?[A-Z][a-zA-Z_]*) *\( *([a-zA-Z0-9_, ]+) *\)')
    initialStateRegex = re.compile('init(ial state)?:', re.IGNORECASE)
    goalStateRegex = re.compile('goal( state)?:', re.IGNORECASE)
    actionStateRegex = re.compile('actions:', re.IGNORECASE)
    precondRegex = re.compile('pre(conditions)?:', re.IGNORECASE)
    postcondRegex = re.compile('post(conditions)?:', re.IGNORECASE)
    x = 1
    w.addLiteral("floor")
    initialState = "Initial state: "
    goalState = "Goal state: "
    with open(filename) as f:
        for line in f:
            if x == 1:
                literals = list(map(int, (line.split(" "))))
                for i in range(literals[0]):
                    w.addLiteral(("r" + str(i + 1)))
                for i in range(literals[1]):
                    w.addLiteral(("b" + str(i + 1)))
            elif(x == 2):
                global planner
                planner = line[0]

            elif(x == 4 or x==6):
                tempState = line.replace("(on shakey ", "Onshakey(")
                tempState = tempState.replace("(at shakey ", "Atshakey(")
                tempState = tempState.replace("(at ", "At(")
                tempState = tempState.replace("(switchon ", "Switchon(")
                tempState = tempState.replace("~", "!")
                tempState = tempState.replace(")", "),")
                tempState = tempState.replace("l", "r")
                tempState = tempState.replace("froor", "floor")
                if(x == 4):
                    initialState = initialState + tempState[0:-2]
                else:
                    goalState = goalState + tempState[0:-2]
            x += 1

    m = initialStateRegex.match(initialState)
    preds = re.findall(predicateRegex, initialState[len(m.group(0)):].strip())
    for p in preds:
        name = p[0]
        literals = tuple([s.strip() for s in p[1].split(" ")])
        if name[0] == '!':
            name = name[1:]
            w.removeClause(name, literals)
        else:
            w.addClause(name, literals)

    m = goalStateRegex.match(goalState)
    preds = re.findall(predicateRegex, goalState[len(m.group(0)):].strip())
    for p in preds:
        name = p[0]
        literals = tuple([s.strip() for s in p[1].split(" ")])
        truth = name[0] != '!'
        if not truth:
            name = name[1:]
        w.addGoal(name, literals, truth)

    filename = "action.txt"
    x = 1
    cur_action = None
    with open(filename) as f:
        for line in f:
            if(x % 3 == 1):
                m = predicateRegex.match(line.strip())
                name = m.group(1)
                params = tuple([s.strip() for s in m.group(2).split(",")])
                cur_action = Action(name, params, [], [])
            elif(x % 3 == 2):
                m = precondRegex.match(line.strip())
                preds = re.findall(predicateRegex, line[len(m.group(0)):].strip())
                for p in preds:
                    name = p[0]
                    params = tuple([s.strip() for s in p[1].split(",")])
                    truth = name[0] != '!'
                    if not truth:
                        name = name[1:]
                    cur_action.pre.append(Clause(name, params, truth))
            else:
                m = postcondRegex.match(line.strip())
                preds = re.findall(predicateRegex, line[len(m.group(0)):].strip())
                for p in preds:
                    name = p[0]
                    params = tuple([s.strip() for s in p[1].split(",")])
                    truth = name[0] != '!'
                    if not truth:
                        name = name[1:]
                    cur_action.post.append(Clause(name, params, truth))
                w.addAction(cur_action)
            x += 1
    for k, v in w.actions.items():
        v.allPossActions(w)
    return w

def doesOppose(state, action):
    for post in action.post:
        m = findClause(state, post)
        if m != None and m.truth != post.truth:
            return True
    return False

def satisfied(state, goal):
    condition = findClause(state, goal)
    if goal.truth == True:
        return condition != None
    return condition == None

def numPreAbsent(state, preconds):
    count = 0
    for p in preconds:
        if not satisfied(state, p):
            count += 1
    return count

def preReachable(world, action):
    for p in action.pre:
        if not clauseReachable(world, p):
            return False
    return True

def clauseReachable(world, clause):
    if clause.inCurState(world):
        return True

    for key,action in world.actions.items():
        for eachAction in action.allActions:
            for p in eachAction.post:
                if compareTruth(p, clause):
                    return True
    return False

def update_state(state, post):
    condition = findClause(state, post)
    if post.truth == True and condition is None:
        state.append(post)
    elif condition != None and post.truth is False:
        state.remove(condition)
    return state

def getAllActions(world, goal):
    results = []
    for key,action in world.actions.items():
        for eachAction in action.allActions:
            for p in eachAction.post:
                if compareTruth(p, goal):
                    results.append(eachAction)
                    break
    return results

def getAllStateActions(world, state):
    results = []
    for key,action in world.actions.items():
        for eachAction in action.allActions:
            c = True
            for p in eachAction.pre:
                if not satisfied(state, p):
                    c = False
                    break
            if(c):
                results.append(eachAction)
    return results
q = queue.Queue()
ac = queue.Queue()
nActions = 0
def calAction(goalst):
    global nActions
    result = []
    while(parent[goalst] != ' '):
        result.append(actionReq[goalst])
        goalst = parent[goalst]
    for i in range(len(result)):
        print (result[len(result) - i - 1])
        nActions += 1
    return result
def solvePlanner(world):
    global nActions
    state = []
    for predicate in world.state:
        for literals in world.state[predicate]:
            state.append(Clause(predicate, literals, True))

    goals = list(world.goals)
    if(planner == "f"):
        q.put(state)
        goalst =  forwardPlanner(world, state, goals, [])
        if(len(goalst) > 0):
            print("Solution found")
            resultaction = calAction(goalst)
        else:
            print("No soltuion")
        visited.clear()
    else:
        solution =  goalStackPlanner(world, state, goals, [])
        if(solution != None):
            print("Soltuion found")
            print_plan(solution)
        else:
            print("No solution")

nodesExpanded = 0
def goalStackPlanner(world, state, goals, current_plan, depth = 0):
    global nodesExpanded
    x = [str(state[e]) for e in range(len(state))]
    x.sort()
    plan = []
    if len(goals) == 0:
        return plan
    i = 0
    while i < len(goals):
        goal = goals[i]
        if satisfied(state, goal):
            i += 1
            continue
        nodesExpanded += 1
        possible_actions = sorted(getAllActions(world, goal), key=lambda c: numPreAbsent(state, c.pre))
        found = False

        for action in possible_actions:
            if not preReachable(world, action):
                continue

            if doesOppose(goals, action):
                continue

            temp_state = list(state)

            subgoals = list(action.pre)

            current_plan.append(action)

            solution = goalStackPlanner(world, temp_state, subgoals, current_plan, depth = depth + 1)

            if solution is None:
                current_plan.pop()
                continue
            for post in action.post:
                update_state(temp_state, post)

            goalsNegated = [x for x in goals[0:i] if x != goal and not satisfied(temp_state, x)]
            tempLen = len(goalsNegated)
            if len(goalsNegated) > 0:
                [goals.remove(x) for x in goalsNegated]
                [goals.append(x) for x in goalsNegated]
                i -= tempLen
            plan.extend(solution)
            del state[:]
            state.extend(temp_state)
            plan.append(action)

            i += 1
            found = True
            break

        if not found:
            return None
    return plan

visited = dict()
parent = dict()
actionReq = dict()
def forwardPlanner(world, state, goals, current_plan, depth = 0):
    global nodesExpanded
    while(not q.empty()):
        state = q.get()

        x = [str(state[e]) for e in range(len(state))]
        x.sort()
        st = ''
        st = ''.join(x)

        if(depth == 0):
            parent[st] = ' '
        depth += 1
        global visited
        if(st in visited):
            continue
        visited[st] = True

        c = 0
        i = 0
        while i < len(goals):
            goal = goals[i]
            if satisfied(state, goal):
                c += 1
            i += 1
        if(c == len(goals)):
            return st
        nodesExpanded += 1
        possible_actions = sorted(getAllStateActions(world, state), key=lambda c: numPreAbsent(goals, c.post))
        for action in possible_actions:
            temp_state = list(state)
            for post in action.post:
                update_state(temp_state, post)
            x2 = [str(temp_state[e]) for e in range(len(temp_state))]
            x2.sort()
            st2 = ''.join(x2)
            if(st2 not in visited):
                q.put(temp_state)
                parent[st2] = st
                actionReq[st2] = str(action.simple_str())
            temp_state = None
    return ''

def forwardPlannerDFS(world, state, goals, current_plan, depth = 0):
    global nodesExpanded
    x = [str(state[e]) for e in range(len(state))]
    x.sort()
    st = ''
    st = ''.join(x)
    if(st in visited):
        return None
    visited[st] = True
    c = 0
    i = 0
    while i < len(goals):
        goal = goals[i]
        if satisfied(state, goal):
            c += 1
        i += 1
    if(c == len(goals)):
        return current_plan
    nodesExpanded += 1
    possible_actions = sorted(getAllStateActions(world, state), key=lambda c: numPreAbsent(goals, c.post))
    for action in possible_actions:
        temp_state = list(state)
        for post in action.post:
            update_state(temp_state, post)
        solution = forwardPlannerDFS(world, temp_state, goals, current_plan + [action], depth + 1)
        temp_state = None
        if(solution != None):
            return solution
    return None

def print_plan(plan):
    global nActions
    for x in plan:
        print(x.simple_str())
        nActions += 1

def main():
    start_time = time.time()
    w = createWorld()
    already_solved = w.goalReached()
    print ("Goal already solved? {0}".format(already_solved))
    if not already_solved:
        print ("Solving...")
        solvePlanner(w)
    print("{0} Actions".format(nActions))
    print("{0} Nodes Expanded".format(nodesExpanded))
    print("{0} seconds".format(time.time() - start_time))
if __name__ == "__main__":
    main()
