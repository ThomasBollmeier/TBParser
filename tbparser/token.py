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
    
class Prefix(TokenType):
    
    def __init__(self, tokenText):
        
        TokenType.__init__(self)
        
        regexStr = r"\A(%s)(\S+)\Z" % self._escape(tokenText)
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
    
    def __init__(self, tokenText):
        
        TokenType.__init__(self)
        
        regexStr = r"\A(\S+)(%s)\Z" % self._escape(tokenText)
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
    
    def __init__(self, tokenText, whitespaceAllowed=True):
        
        TokenType.__init__(self)
        
        tmp = self._escape(tokenText)
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


