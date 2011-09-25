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

import re

class Token(object):
    
    def __init__(self, text, types):
        
        self._text = text
        self._types = types
        
    def getText(self):
        
        return self._text
    
    def getTypeIds(self):
        
        return [type_.getId() for type_ in self._types]
        
    def getTypes(self):
        
        return self._types
        
class TokenType(object):
    
    currentId = 0
    
    def __init__(self):
        
        if self.__class__ == TokenType:
            raise AbstractInstantiationError
        
        TokenType.currentId += 1
        self._id = TokenType.currentId
        self._len = 0
        
    def getId(self):
        
        return self._id
    
    def createToken(self, text):
        
        raise NotImplementedError

    @staticmethod
    def compare(tokenType_1, tokenType_2):
    
        if tokenType_1._len > tokenType_2._len:
            return -1
        elif tokenType_1._len < tokenType_2._len:
            return 1
        else:
            return 0

    def _escape(self, text):
        
        for ch in ['+', '*', '.']:
            text = text.replace(ch, '\\' + ch)
    
        return text
    
class Word(TokenType):
    
    def __init__(self, pattern):
        
        TokenType.__init__(self)
        
        self._regex = re.compile(r"\A(%s)\Z" % pattern)
        self._len = len(pattern)
        
    def createToken(self, text):
        
        match = self._regex.match(text)
        if match:
            return Token(match.group(1), [self])
        else:
            return None
        
    def matches(self, text):
        
        return bool(self._regex.match(text))
        
class Keyword(TokenType):
    
    def __init__(self, keyword):
        
        TokenType.__init__(self)
        
        self._keyword = keyword
        
    def getKeyword(self):
        
        return self._keyword
    
    def createToken(self, text):
        
        if text == self._keyword:
            return Token(text, [self])
        else:
            return None
        
class Literal(TokenType):
    
    DELIMITERS = ['\'', '\"']
    
    _single = None
    
    @staticmethod
    def get():
        
        if not Literal._single:
            Literal._single = Literal()
            
        return Literal._single
    
    def __init__(self):
        
        TokenType.__init__(self)
        
    def createToken(self, text):
        
        if self.isLiteral(text):
            return Token(text, [self])
        else:
            return None
        
    def isLiteral(self, text):
        
        if len(text) >= 2:
            first = text[0]
            return (first in Literal.DELIMITERS) and (text[-1] == first)
        else:
            return False
    
class Prefix(TokenType):
    
    def __init__(self, tokenText, escape=True):
        
        TokenType.__init__(self)
        
        if escape:
            tmp = self._escape(tokenText)
        else:
            tmp = tokenText
        
        regexStr = r"\A(%s)(\S+)\Z" % tmp 
        self._regex = re.compile(regexStr)
        self._len = len(tokenText)
    
    def createToken(self, text):
        
        match = self._regex.match(text)

        if match:
            return Token(match.group(1), [self])
        else:
            return None
            
    def getRemainingRight(self, text):

        match = self._regex.match(text)

        if match:
            return match.group(2)
        else:
            return ""

class Postfix(TokenType):
    
    def __init__(self, tokenText, escape=True):
        
        TokenType.__init__(self)

        if escape:
            tmp = self._escape(tokenText)
        else:
            tmp = tokenText
        
        regexStr = r"\A(\S+)(%s)\Z" % tmp
        self._regex = re.compile(regexStr)
        self._len = len(tokenText)
    
    def createToken(self, text):
        
        match = self._regex.match(text)

        if match:
            return Token(match.group(2), [self])
        else:
            return None
            
    def getRemainingLeft(self, text):

        match = self._regex.match(text)

        if match:
            return match.group(1)
        else:
            return ""
   
class Separator(TokenType):
    
    @staticmethod
    def create(pattern):
        
        res = Separator('')
        res._regex = re.compile(pattern)
        res._len = len(pattern)
        
        return res
                   
    def __init__(self, tokenText, whitespaceAllowed=True, escape=True):
        
        TokenType.__init__(self)
        
        if escape:
            tmp = self._escape(tokenText)
        else:
            tmp = tokenText
        
        if whitespaceAllowed:
            regexStr = r"\A(.*)(" + tmp + ")(.*)\Z"
        else:
            regexStr = r"\A(\S+)(" + tmp + ")(\S+)\Z"
        self._regex = re.compile(regexStr)
        self._len = len(tokenText)
    
    def createToken(self, text):
        
        match = self._regex.match(text)

        if match:
            return Token(match.group(2), [self])
        else:
            return None
            
    def getRemainingLeft(self, text):

        match = self._regex.match(text)

        if match:
            return match.group(1)
        else:
            return ""

    def getRemainingRight(self, text):

        match = self._regex.match(text)

        if match:
            return match.group(3)
        else:
            return ""
        
class AbstractInstantiationError(Exception):
    pass


