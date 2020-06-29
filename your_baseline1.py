# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

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
        #print(features*weights)
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

    def getFeatures(self, gameState, action):
            #Counter의 인스턴스로 features를 생성한다.
            features = util.Counter()
            #gameState와, action에 따른 successor이다.
            successor = self.getSuccessor(gameState, action)
            #먹어야할 food list이다.
            foodList = self.getFood(successor).asList()
            #features의 successorScore는 foodList의 개수의 마이너스를 곱한것이다.
            #Food의 개수를 하나의 인자로 받는다.
            features['successorScore'] = len(foodList)  # self.getScore(successor)
            # Compute distance to the nearest food
            #만약, foodList가 한개라도 존재한다면 -> 즉, 완전히 food를 다 먹지 않는이상, 항상 true이다.
            if len(foodList) > 0:  # This should always be True,  but better safe than sorry
                #Agent의 위치값을 반환한다.
                myPos = successor.getAgentState(self.index).getPosition()
                #foodlist에서 각 food와 Agent의 위치를 구하고, 그 중 최소를 minDistance로 칭한다.
                minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
                #그 minDistance값을 features의 distanceToFood값으로 넣는다.
                features['distanceToFood'] = minDistance
            #myOpponents라는 list를 생성한다.
            myOpponents = []
            for i in self.getOpponents(successor):
                myOpponents.append(successor.getAgentState(i))
            #myOpponents중 실제 위협이 되는 myOpponents_danger list를 생성한다.
            myOpponents_danger = []
            #myOpponents에서 팩맨이 아닌것, 즉 고스트는 위협이 되므로, 리스트에 추가한다.
            for myOpponent in myOpponents:
                if myOpponent.isPacman:
                    pass
                else:
                    myOpponents_danger.append(myOpponent)
            #distance list를 생성한다.
            distance=[]
            #distance list에 실제 위협이 되는 myOpponents_danger들과 나의 거리를 저장한다.
            for i in myOpponents_danger:
                distance.append(self.getMazeDistance(myPos, i.getPosition()))
            #distance값 중 가장 작은 것을 feature의 myOpponent_distance로 추가한다.
            features['myOpponent_distance'] = min(distance)
            #print(min(distance))
            #distance가 6 이하인 경우 본격적인 위협이 된다고 고려하고, 6이하인 것이 있으면
            #real_danger_distance feature값을 10으로 둔다.
            for i in distance:
                if i<=6:
                    features['real_danger_distance'] = 10
            return features

    def getWeights(self, gameState, action):
        return {'successorScore': -100, 'distanceToFood': -4, 'myOpponent_distance': -10, 'real_danger_distance': -300}


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
