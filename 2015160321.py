from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint
from capture import GameState


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
        features['successorScore'] = -len(foodList)



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

        # 하프라인을 리스트로 받는다
        halfline = []
        if self.red:
            # 좌표가 0부터 시작하기 때문에, red팀이라면 전체 폭의 절반에서 1을 뺀것이 하프라인이다.
            halfline_x = gameState.data.layout.width // 2 - 1
        else:
            halfline_x = gameState.data.layout.width // 2
        # 벽이 아닌 부분만을 찾아내서 하프라인 리스트에 추가한다.
        for i in range(gameState.data.layout.height):
            if gameState.data.layout.walls[halfline_x][i]:
                pass
            else:
                halfline.append(((halfline_x), i))
        # 현재 위치와 가장 가까운 하프라인의 거리를 goinghomeDistance로 둔다.
        tmp = []
        for i in halfline:
            tmp.append(self.getMazeDistance(myPos, i))
        goinghomeDistance = min(tmp)
        features['goinghomedistance'] = goinghomeDistance
        # disttoscore = min([self.getMazeDistance(myPos, scorespot) for scorespot in halfline])
        # features['distToScore'] = disttoscore

        capsuleList = self.getCapsules(successor)
        if len(capsuleList) > 0:
            minCapDistance = min([self.getMazeDistance(myPos, capsule) for capsule in capsuleList])
            if features['real_danger_distance'] == -1:
                features['distanceToCapsule'] = minCapDistance
            else:
                features['distanceToCapsule'] = 10 * minCapDistance

        # stop을 feature에 만들어서, action이 stop direction이면, 가중치 1을 준다.
        # stop의 weight는 음수이다.
        # reverse역시, 가중치를 1을 주고, weight는 음수이다.
        features['stop'] = 0
        if action == Directions.STOP:
            features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        features['reverse'] = 0
        if action == rev:
            features['reverse'] = 1

        # 뒤에 고스트가 따라올때, 막다른 골목에 접어들지 않아야 한다.
        # 아래 코드는 막다른 골목으로 가지 않기 위한 코드이다.
        # 우선, feature의 safety를 0으로 둔다. 이것이 안전한 상태인데, 안전하지 않으면 1로 바뀐다.
        features['safety'] = 0
        successor = self.getSuccessor(gameState, action)
        legalActions = successor.getLegalActions(self.index)
        # 가능한 액션의 수를 받는다.
        Actionlength = len(legalActions)
        OppositeAction = {"East": "West", "West": "East", "South": "North", "North": "South", "Stop": "Stop"}
        # 만약 유령과의 거리가 4 미만이라면 아래 코드를 진행한다.
        if min(distance) < 6:
            # 가능한 action이 3보다 적으면, safety가 1이 된다.
            if Actionlength < 3:
                features['safety'] = 1
            else:
                # 액션의 수가 3보다 크다는것은 사방이 뚫린 곳이라는 의미이므로 패스해도 좋다.
                if Actionlength > 3:
                    pass
                # 액션의 수가 3이면 다음과 같이 진행한다.
                else:
                    # depth를 0으로 두고, while문 안에서 1씩 증가하면서 골목 안쪽으로 접근한다.
                    depth = 0
                    # depth가 4 미만일때 진행한다.
                    while depth < 4:
                        # 만약 actionlength가 3 미만인것이 발견되면, 즉시 safety를 1로 둔다.
                        if Actionlength < 3:
                            features['safety'] = 1
                            break
                        # actionlength가 3이어도, 안쪽을 더 살펴봐야한다.
                        else:
                            # 액션과 반대의 액션을 받는다.
                            oppositeAction = OppositeAction[action]
                            # cantgo라는 집합은, stop과 oppositeAction의 집합이다.
                            cantgo = set(["Stop", oppositeAction])
                            # cango는 가능한 액션에서 cantgo를 뺀 것, 즉 갈 수 있는 곳이다.
                            cango = set(legalActions) - cantgo
                            # 하나를 pop해서 cango를 얻는다.
                            cango = cango.pop()

                            # 이제 actionlength를 다시 받는다.
                            successor = successor.generateSuccessor(self.index, cango)
                            legalActions = successor.getLegalActions(self.index)
                            Actionlength = len(legalActions)
                        # depth를 1 추가한다.
                        depth += 1
        else:
            pass



        return features

    def getWeights(self, gameState, action):
        # getWeights에서는, enemy 고스트가 가까워졌을 때, 빨리 본진으로 돌아가도록 한다.
        successor = self.getSuccessor(gameState, action)
        successorposition = successor.getAgentState(self.index).getPosition()

        # enemy 중에서 고스트 형태인 것들의 리스트를 받는다.
        myOpponents = []
        for i in self.getOpponents(successor):
            if successor.getAgentState(i).isPacman:
                pass
            else:
                myOpponents.append(successor.getAgentState(i))
        # 고스트 중에서 가장 가까운 것을 min_distance로 정의한다.
        if myOpponents:
            min_distance = min([self.getMazeDistance(successorposition, j.getPosition()) for j in myOpponents])
            # 그런데, 이 min_distance가 8보다 작으면, 즉 어느정도 가까우면,
            # agent가 운반하는 food가 많을수록 책임이 크므로 얼른 돌아가야 하고,
            # min_distance가 작을수록 위험하므로 얼른 돌아가야한다.
            if min_distance < 9:
                parameter = gameState.getAgentState(self.index).numCarrying
                GoHome = -10 * parameter // min_distance
            else:
                GoHome = 0
        # 시간을 체크한다. 남은시간이 100아래로 떨어지면, GoHome을 -30000으로 둔다.
        if gameState.data.timeleft > 100:
            pass
        else:
            #print("ooo")
            GoHome = -30000

        return {'successorScore': 100, 'distanceToFood': -4, 'goinghomedistance': GoHome, 'myOpponent_distance': 1,
                'real_danger_distance': -100, 'stop': -400, 'reverse': -50, 'distanceToCapsule': -2, 'safety': -1000}


class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.  It is not the best or only way to make
    such an agent.
    """

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)

        # 하프라인을 리스트로 받는다
        self.halfline = []
        if self.red:
            # 좌표가 0부터 시작하기 때문에, red팀이라면 전체 폭의 절반에서 3을 뺀것이 하프라인이다.
            halfline_x = gameState.data.layout.width // 2 - 3
        else:
            halfline_x = gameState.data.layout.width // 2 + 1
        # 벽이 아닌 부분만을 찾아내서 하프라인 리스트에 추가한다.
        for i in range(gameState.data.layout.height):
            if gameState.data.layout.walls[halfline_x][i]:
                pass
            else:
                self.halfline.append(((halfline_x), i))
        #x와 y라는 변수를 halfline list의 요소 중 다음과 같은 것으로 저장한다.
        #print(self.halfline)
        x, y = self.halfline[3*len(self.halfline) // 4]
        self.place = (x, y)
        self.x, self.y = gameState.getWalls().asList()[-1]

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        mystate = successor.getAgentState(self.index)
        mypos = mystate.getPosition()

        #상대편 agent를 파악한다.
        #상대편 agent가 우리 구역으로 넘어오면, real_opponent 리스트에 추가한다.
        opponent=[]
        real_opponent=[]
        for i in self.getOpponents(successor):
            opponent.append(successor.getAgentState(i))
            if opponent[-1].isPacman and opponent[-1].getPosition()!=None:
                real_opponent.append(opponent[-1])
        #만약 우리 구역에 넘어온 상대 agent가 있는 경우, real_opponent_num을 1로 활성화한다.
        if len(real_opponent)==0:
            features['real_opponent_num']=0
        else:
            features['real_opponent_num']=1
        #features['real_opponent_num'] = len(real_opponent)

        # 상대편 ghost가 내 진영에 들어왔을 때, 내 포지션은 그 ghost를 향해 가야한다.
        if len(real_opponent) > 0:
            for e in real_opponent:
                self.place = e.getPosition()

        # Dis라는 feature가 현 위치와, self.place간의 거리를 나타낸다.
        features['Dis'] = self.getMazeDistance(mypos, self.place)

        # mypos가 self.place에 속해있다면
        if mypos in self.place:
            # self.place는 하프라인으로 잡은 리스트의 정해진 지점으로 움직인다.
            # 즉, 그곳에서 자리를 지킨다.
            self.place = self.halfline[4 * len(self.halfline) // 6]

        #reverse에 대한 feature이다.
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev:
            features['reverse'] = 1

        #상대편 고스트 agent가 들어왔을 때, 하프라인 어느지점으로 가서 방어할 것인지를 파악해야한다.
        distanceToEnemy = []
        #real_opponent가 있을 때,
        if len(real_opponent) > 0:
            for i in real_opponent:
                #내 위치와 real_opponent와의 거리가 distanceToEnemy다.
                distanceToEnemy=self.getMazeDistance(mypos, i.getPosition())
                features['distanceToEnemy'] = distanceToEnemy
            #하프라인 지점들에 대해서, 상대방 agent와의 거리를 구한다.
            for position in self.halfline:
                #maximum을 10000으로 두고, 각 하프라인 지점과 agent와의 거리를 구해서, 어느 지점에서 가장 최소 거리인지를 잡는다.
                maximum = 10000
                if self.getMazeDistance(position, real_opponent[-1].getPosition()) < distanceToEnemy:
                    tmp = self.getMazeDistance(position, real_opponent[-1].getPosition())
                    #maximum보다 tmp가 작으면, 그 tmp값이 다시 maximum이 된다.
                    if tmp < maximum:
                        maximum = tmp
                    #최종적으로 가야할 위치가 바로 havetogo다.
                    havetogo = position
                #만약 enemy와의 거리가 9미만, 그리고 위에서 구했던 maximum이상이라면, havetogo로 이동한다.
                if distanceToEnemy < 9 and distanceToEnemy >= maximum:
                    # Go to that point to intercept
                    self.place = havetogo

        return features

    def getWeights(self, gameState, action):
        return {'real_opponent_num': -500, 'Defense': 100,  'Dis': -1,
                           'reverse': -2, 'distanceToEnemy': -15}

