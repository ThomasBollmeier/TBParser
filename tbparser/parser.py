# coding=UTF-8

# This file is part of TBParser.
#
# TBParser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TBParser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TBParser.  If not, see <http://www.gnu.org/licenses/>.

from tbparser.lexer import Lexer
from tbparser.instream import FileInput, StringInput
from tbparser.token import Keyword
from tbparser.grammar import SuccessorError

class Parser(object):

    def __init__(self, grammar):

        self._grammar = grammar
        self._lexer = Lexer()
        for tt in self._grammar.getTokenTypes():
            self._lexer.addTokenType(tt)
        
    def enableLineComments(self, lineCommentStart='//'):
        
        self._lexer.enableLineComments(lineCommentStart)
                

    def enableBlockComments(self,
                            blockCommentStart='/*', 
                            blockCommentEnd='*/'
                            ):

        self._lexer.enableBlockComments(blockCommentStart, blockCommentEnd)

    def parse(self, inStream):
        
        self._lexer.setInputStream(inStream)
        self._tokenBuffer = []
        path = Path()
        path.push(self._grammar.getSocket(), None)
        error = False
        done = False

        while not done:
            
            token = self._getNextToken()
            
            if not token:

                found, path = self._findPathToEnd(path)
                
                if found:
                    done = True    
                else:
                    found, path = self._findNextSibling(path)
                    if not found:
                        error = True
                        done = True

                continue
 
            found, path = self._findNextMatchingNode(token, path)
            
            if found:
                self._tokenBuffer.pop()
            else:
                found, path = self._findNextSibling(path)
                if not found:
                    done = True
                    error = True
        
        if not error:
            return self._createAst(path)
        else:
            if self._tokenBuffer:
                token = self._tokenBuffer[0] 
                text = token.getText()
                line, column = token.getStartPosition()
                raise ParseError(line, column, text)
            else:
                raise Exception("Parsing error")

    def parseFile(self, filePath):

        return self.parse(FileInput(filePath))

    def parseString(self, string):

        return self.parse(StringInput(string))

    def _createAst(self, path):

        stack = []
        current = None

        numElements = path.getLength()

        for i in range(numElements):

            element = path.getElement(i)
            node = element.getGrammarNode()
            token = element.getToken()

            if node.isRuleStart():

                if current:
                    stack.append(current)
                name = node.getName()
                id_ = node.getId()    
                text = token and token.getText() or ''
                current = AstNode(name, text, id_)

            elif node.isRuleEnd():

                # Ggf. Transformation. Dabei ID aus Regel bewahren:
                tmp = current;
                current = node.transform(current)
                if current is not tmp:
                    current.setId(tmp.getId())
                
                parent = stack and stack.pop() or None
                if parent:
                    parent.addChild(current)
                    current = parent
                else:
                    break

            elif node.isTokenNode():

                id_ = node.getId()
                text = token and token.getText() or ''
                current.addChild(AstNode('token', text, id_))

            else:
                continue

        return current

    def _findNextSibling(self, path):
        
        removed = []
        
        while True:

            if path.getLength() < 2:
                # Ursprünglichen Pfad wiederherstellen:
                while removed:
                    elem = removed.pop()
                    token = elem.getToken()
                    if token:
                        self._tokenBuffer.pop()
                    path.push(elem.getGrammarNode(), token)
                
                return False, path

            siblingFound, path = self._gotoNextSibling(path)
            
            if siblingFound:
                return True, path
            else:
                elem = path.pop()
                token = elem.getToken()
                removed.append(elem)
                if token:
                    self._tokenBuffer.append(token)
 
    def _gotoNextSibling(self, path):
            
        if path.getLength() < 2:
            return False, path

        elem = path.pop()
        start = elem.getGrammarNode()
        token = elem.getToken()

        prev = path.getElement(-1).getGrammarNode()
        context = Context(path, token)

        try:
            successors = prev.getSuccessors(context)
        except SuccessorError:
            path.push(start, token)
            return False, path
        
        try:
            idx = successors.index(start)
            if idx < len(successors) - 1:
                sibling = successors[idx+1]
                if token:
                    self._tokenBuffer.append(token)
                path.push(sibling, None)
                return True, path
            else:
                path.push(start, token)
                return False, path
        except ValueError:
            path.push(start, token)
            return False, path

    def _getNextToken(self):
        
        if not self._tokenBuffer:
            token = self._lexer.getNextToken();
            if token:
                self._tokenBuffer.append(token)

        if self._tokenBuffer:
            return self._tokenBuffer[-1]
        else:
            return None

    def _findNextMatchingNode(self, token, path):
        
        elem = path.getElement(-1)
        startNode = elem.getGrammarNode()
        startToken = elem.getToken()
        
        if startNode.isTokenNode() and startToken is None:
            
            if startNode.getTokenTypeId() in token.getTypeIds():
                path.pop()
                path.push(startNode, token)
                return True, path
            else:
                return False, path

        try:
            successors = startNode.getSuccessors(Context(path, token))
        except SuccessorError:
            return False, path

        for succ in successors:
            
            path.push(succ, None)

            found, path = self._findNextMatchingNode(token, path);
            if found:
                return found, path
            else:
                path.pop()
    
        return False, path
    
    def _findPathToEnd(self, path):

        node = path.getElement(-1).getGrammarNode()
        try:
            successors = node.getSuccessors(Context(path))
        except SuccessorError:
            return False, path

        if not successors:
            return True, path # Fertig!

        for succ in successors:
            
            if succ.isTokenNode():
                continue

            path.push(succ, None)

            found, path = self._findPathToEnd(path);
            if found:
                return found, path
            else:
                path.pop()
    
        return False, path

class PathElement(object):

    def __init__(self, grammarNode, token):

        self._grammarNode = grammarNode
        self._token = token

    def getGrammarNode(self):

        return self._grammarNode

    def getToken(self):

        return self._token

    def getMatchedTokenType(self):

        return self._grammarNode.getTokenType()
        
class Path(object):

    def __init__(self):

        self._elements = []
        self._envStack = [] # Stack der Umgebungen

    def push(self, grammarNode, token):
        
        self._elements.append(PathElement(grammarNode, token))
        
        if grammarNode.isRuleStart():
            self._envStack.append(grammarNode.getEnvVars())
        elif grammarNode.isRuleEnd():
            self._envStack.append(False)
        elif grammarNode.isTokenNode() and grammarNode.changesEnv():
            envVars = self._getCurEnvVars()
            if envVars is not None:
                grammarNode.changeEnv(envVars, token)

    def pop(self):

        res = self._elements.pop()
        
        node = res.getGrammarNode()
        if node.isRuleStart() or node.isRuleEnd():
            self._envStack.pop()
        elif node.isTokenNode() and node.changesEnv():
            envVars = self._getCurEnvVars()
            if envVars is not None:
                node.changeEnv(envVars, res.getToken())
                
        return res;

    def popToken(self):

        element = self.pop()

        return element.getToken()

    def getLength(self):

        return len(self._elements)

    def getElement(self, index):

        numElements = len(self._elements)

        if index < 0:
            index = numElements + index

        if index < 0 or index > numElements - 1:
            raise Exception('Invalid path element index')
        
        return self._elements[index]
        
    def getEnvVar(self, name):
        
        envVarStack = []
        
        for env in self._envStack:
            if not isinstance(env, bool):
                envVarStack.append(env)
            else:
                envVarStack.pop()

        idx = len(envVarStack) - 1
        while (idx > -1):
            if name in envVarStack[idx]:
                return envVarStack[idx][name]
            idx -= 1
            
        return None
 
    def _getCurEnvVars(self):
        
        idx = len(self._envStack) - 1
        level = 0
        while (idx >= 0):
            envVars = self._envStack[idx]
            if not isinstance(envVars, bool):
                if level == 0:
                    return envVars
                level += 1
            else:
                level -= 1
            idx -= 1
        
        return None

    def __repr__(self):

        res = ""

        for elem in self._elements:

            token = elem.getToken()
            if token:
                text = token.getText()
                if res:
                    res += "."
                res += text

        return res
    
    def __str__(self):
        
        res = ''
        for elem in self._elements:
            node = elem.getGrammarNode()
            if res:
                res += ':'
            res += "%d" % node.getTechnicalId()
            
        return res
    
class Context(object):

    def __init__(self, path, token=None):

        self._path = path
        self._token = token
                           
    def setToken(self, token):
        
        self._token = token
        
    def getToken(self):
        
        return self._token
    
    token = property(getToken)

    def getEnvVar(self, name):
        
        return self._path.getEnvVar(name)
        
    def __getitem__(self, name):
        
        return self.getEnvVar(name)
    
    def getCurKeyword(self):
        
        if not self._token:
            return None
        
        for tokenType in self._token.getTypes():
            if isinstance(tokenType, Keyword):
                return tokenType
        
        return None
     
class AstNode(object):

    def __init__(self, name='', text='', identifier=''):

        self._name = name
        self._text = text
        self._id = identifier
        
        self._parent = None
        self._children = []
    
    def copy(self):

        res = AstNode(self._name, self._text, self._id)
        res._children = self._children

        return res

    def addChild(self, child):
            
        self._children.append(child)
        child._parent = self
        
    def removeChildren(self):
        
        for child in self._children:
            child._parent = None
        self._children = []
        
    def replaceChild(self, old, new):

        idx = self._children.index(old)
        self._children[idx] = new
        
    def setName(self, name):
        
        self._name = name

    def getName(self):
            
        return self._name

    def getText(self):
            
        return self._text
    
    def getParent(self):
        
        return self._parent
            
    def getChildren(self):

        return self._children

    def getChildrenByName(self, name):

        return [child for child in self._children if child._name == name]

    def getChild(self, name):

        for child in self._children:
            if child._name == name:
                return child

        return None
    
    def setId(self, identifier):
        
        self._id = identifier
    
    def getId(self):
        
        return self._id;    
    
    def getChildById(self, identifier):
        
        for child in self._children:
            if child._id == identifier:
                return child
        
        return None
    
    def getChildrenById(self, identifier):
        
        return [c for c in self._children if c._id == identifier]
           
    def hasChildren(self):

        return bool(self._children)

class ParseError(Exception):
    
    def __init__(self, line, column, tokenText):
        
        self.line = line
        self.column = column
        self.tokenText = tokenText
        
    def __str__(self):
        
        return "Line:%d, Column:%d -> Unexpected token '%s'" \
            % (self.line, self.column, self.tokenText)
