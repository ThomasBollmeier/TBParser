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
                elif not self._findNextSibling(path):
                    error = True
                    done = True

                continue
 
            found, path = self._findNextMatchingNode(token, path)
            
            if found:
                self._tokenBuffer.pop()
            elif not self._findNextSibling(path):
                done = True
                error = True
        
        if not error:
            return self._createAst(path)
        else:
            if self._tokenBuffer:
                text = self._tokenBuffer[0].getText()
                raise Exception("Unexpected token '%s'" % text)
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
            ttype = element.getMatchedTokenType()
            token = element.getToken()

            if node.isRuleStart():

                if current:
                    stack.append(current)
                name = node.getName()
                id_ = node.getId()    
                text = self._getMatchedText(token, ttype)
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
                text = self._getMatchedText(token, ttype)
                current.addChild(AstNode('token', text, id_))

            else:
                continue

        return current

    def _findNextSibling(self, path):

        while True:

            if path.getLength() < 2:
                return False

            siblingFound, path = self._gotoNextSibling(path)
            
            if siblingFound:
                return True
            else:
                token = path.popToken()
                if token:
                    self._tokenBuffer.append(token)
 
    def _getMatchedText(self, token, matchedType):

        if not token:
            return ''        

        tmp = matchedType.createToken(token.getText())
        
        return tmp  and tmp.getText() or ''
    
    def _gotoNextSibling(self, path):
            
        if path.getLength() < 2:
            return False, path

        elem = path.getElement(-1)
        start = elem.getGrammarNode()
        token = elem.getToken()

        newPath = path.copy()
        newPath.pop()
        prev = newPath.getElement(-1).getGrammarNode()
        context = Context(newPath)

        successors = prev.getSuccessors(context)
        try:
            idx = successors.index(start)
            if idx < len(successors) - 1:
                sibling = successors[idx+1]
                if token:
                    self._tokenBuffer.append(token)
                newPath.push(sibling, None)
                return True, newPath
            else:
                return False, path
        except ValueError:
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

        successors = startNode.getSuccessors(Context(path))

        for succ in successors:
            
            tmpPath = path.copy()
            tmpPath.push(succ, None)

            found, newPath = self._findNextMatchingNode(token, tmpPath);
            if found:
                return found, newPath
    
        return False, path
    
    def _findPathToEnd(self, path):

        node = path.getElement(-1).getGrammarNode()
        successors = node.getSuccessors(Context(path));

        if not successors:
            return True, path # Fertig!

        for succ in successors:
            
            if succ.isTokenNode():
                continue

            tmpPath = path.copy()
            tmpPath.push(succ, None)

            found, newPath = self._findPathToEnd(tmpPath);
            if found:
                return found, newPath
    
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

    def copy(self):

        clone = Path()
        
        for elem in self._elements:
            clone.push(elem.getGrammarNode(), elem.getToken())

        return clone

    def push(self, grammarNode, token):
        
        self._elements.append(PathElement(grammarNode, token))

    def pop(self):

        return self._elements.pop()

    def popToken(self):

        element = self._elements.pop()

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

    def toString(self):

        res = ""

        for elem in self._elements:

            token = elem.getToken()
            if token:
                text = token.getText()
                if res:
                    res += "."
                res += text

        return res
    
class Context(object):

    def __init__(self, path):

        size = path.getLength()
        self._stack = []
        
        for i in range(size):
            
            node = path.getElement(i).getGrammarNode()

            if node.isRuleStart():
                self._stack.append(node.getEnvVars())
            elif node.isRuleEnd():
                self._stack.pop()

    def getEnvVar(self, name):

        iScope = len(self._stack) - 1
        while (iScope):
            if name in self._stack[iScope]:
                return self._stack[iScope]
            iScope -= 1
            
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
    
    def setName(self, name):
        
        self._name = name

    def getName(self):
            
        return self._name

    def getText(self):
            
        return self._text
            
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
