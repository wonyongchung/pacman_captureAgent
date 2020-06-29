from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='OffensiveReflexAgent', second='DefensiveReflexAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that chooses score-maximizing actions
    """

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = gameState.getLegalActions(self.index)


        values = [self.evaluate(gameState, a) for a in actions]


        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        foodLeft = len(self.getFood(gameState).asList())

        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self, gameState, action):
        """
        Normally, weights do not depend on the gamestate.  They can be either
        a counter or a dictionary.
        """
        return {'successorScore': 1.0}


class OffensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that seeks food. This is an agent
    we give you to get an idea of what an offensive agent might look like,
    but it is by no means the best or only way to build an offensive agent.
    """

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = gameState.getLegalActions(self.index)


        values = [self.evaluate(gameState, a) for a in actions]

        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        foodLeft = len(self.getFood(gameState).asList())

        bestAction = random.choice(bestActions)

        return bestAction

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):

            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        foodList = self.getFood(successor).asList()
        features['successorScore'] = -len(foodList)  # self.getScore(successor)


        if len(foodList) > 0:
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance

        # myOpponents라는 list를 생성한다.
        myOpponents = []
        for i in self.getOpponents(successor):
            myOpponents.append(successor.getAgentState(i))
        # myOpponents중 실제 위협이 되는 myOpponents_danger list를 생성한다.
        myOpponents_danger = []
        # myOpponents에서 팩맨이 아닌것, 즉 고스트는 위협이 되므로, 리스트에 추가한다.
        for myOpponent in myOpponents:
            if myOpponent.isPacman:
                pass
            else:
                myOpponents_danger.append(myOpponent)
        # distance list를 생성한다.
        distance = []
        # distance list에 실제 위협이 되는 myOpponents_danger들과 나의 거리를 저장한다.
        for i in myOpponents_danger:
            distance.append(self.getMazeDistance(myPos, i.getPosition()))
        # distance값 중 가장 작은 것을 feature의 myOpponent_distance로 추가한다.
        features['myOpponent_distance'] = min(distance)
        # distance가 2 이하인 경우 본격적인 위협이 된다고 고려하고, 2이하인 것이 있으면
        # real_danger_distance feature값을 1으로 둔다.
        features['real_danger_distance'] = -1
        for i in distance:
            if i <= 2:
                features['real_danger_distance'] = 1

        #하프라인을 리스트로 받는다
        halfline = []
        if self.red:
            #좌표가 0부터 시작하기 때문에, red팀이라면 전체 폭의 절반에서 1을 뺀것이 하프라인이다.
            halfline_x = gameState.data.layout.width//2 - 1
        else:
            halfline_x = gameState.data.layout.width//2
        #벽이 아닌 부분만을 찾아내서 하프라인 리스트에 추가한다.
        for i in range(gameState.data.layout.height):
            if gameState.data.layout.walls[halfline_x][i]:
                pass
            else:
                halfline.append(((halfline_x), i))
        #현재 위치와 가장 가까운 하프라인의 거리를 goinghomeDistance로 둔다.
        tmp = []
        for i in halfline:
            tmp.append(self.getMazeDistance(myPos, i))
        goinghomeDistance = min(tmp)
        features['goinghomedistance'] = goinghomeDistance
        #disttoscore = min([self.getMazeDistance(myPos, scorespot) for scorespot in halfline])
        #features['distToScore'] = disttoscore

        #stop을 feature에 만들어서, action이 stop direction이면, 가중치 1을 준다.
        #stop의 weight는 음수이다.
        #reverse역시, 가중치를 1을 주고, weight는 음수이다.
        features['stop'] = 0
        if action == Directions.STOP:
            features['stop'] = 1
        reverse_action = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        features['reverse'] = 0
        if action == reverse_action:
            features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        #getWeights에서는, enemy 고스트가 가까워졌을 때, 빨리 본진으로 돌아가도록 한다.
        #successor과
        successor = self.getSuccessor(gameState, action)
        successorposition = successor.getAgentState(self.index).getPosition()

        #enemy 중에서 고스트 형태인 것들의 리스트를 받는다.
        myOpponents = []
        for i in self.getOpponents(successor):
            if successor.getAgentState(i).isPacman:
                pass
            else:
                myOpponents.append(successor.getAgentState(i))
        #고스트 중에서 가장 가까운 것을 min_distance로 정의한다.
        if myOpponents:
            min_distance = min([self.getMazeDistance(successorposition, j.getPosition()) for j in myOpponents])
            #그런데, 이 min_distance가 8보다 작으면, 즉 어느정도 가까우면,
            #agent가 운반하는 food가 많을수록 책임이 크므로 얼른 돌아가야 하고,
            #min_distance가 작을수록 위험하므로 얼른 돌아가야한다.
            if min_distance < 9:
                parameter = gameState.getAgentState(self.index).numCarrying
                GoHome = -15*parameter//min_distance
            else:
                GoHome = 0


        return {'successorScore': 100, 'distanceToFood': -4, 'goinghomedistance': GoHome,'myOpponent_distance': 1,
                'real_danger_distance': -100,  'stop': -400, 'reverse': -50}


class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.  It is not the best or only way to make
    such an agent.
    """

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()


        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0


        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(dists)

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}
