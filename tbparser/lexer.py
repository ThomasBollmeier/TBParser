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
from tbparser.token import Token, TokenType, Keyword, \
Word, Prefix, Postfix, Separator, Literal
from tbparser.input_buffer import InputBuffer

class Lexer(object):
    
    def __init__(self):
        
        self._instream = None
        self._stack = []
        self._keywords = {}
        self._words = []
        self._prefixes = []
        self._postfixes = []
        self._separators = []
        self._literal = None
        self._literalDelims = []
        self._currentLitDelim = ''
        self._wsCharCodes = [
                             WSCharCode.TAB,
                             WSCharCode.LINEBREAK,
                             WSCharCode.VTAB,
                             WSCharCode.FORMFEED,
                             WSCharCode.SPACE
                             ]
        self._mode = LexerMode.NORMAL
        self._lineCommentEnabled = False
        self._lineCommentStart = ''
        self._blockCommentEnabled = False
        self._blockCommentStart = ''
        self._blockCommentEnd = ''
        
        self._line = 1
        self._column = 0

    def setInputStream(self, instream):

        self._instream = instream
        self._reset()
    
    def _reset(self):

        self._stack = []
        self._inputBuffer = None
        self._mode = LexerMode.NORMAL
        self._line = 1
        self._column = 0

    def addTokenType(self, tt):
        
        if isinstance(tt, Keyword):
            self._keywords[tt.getKeyword()] = tt
        elif isinstance(tt, Word):
            self._words.append(tt)
        elif isinstance(tt, Prefix):
            self._prefixes.append(tt)
            self._prefixes.sort(cmp=TokenType.compare)
        elif isinstance(tt, Postfix):
            self._postfixes.append(tt)
            self._postfixes.sort(cmp=TokenType.compare)
        elif isinstance(tt, Separator):
            self._separators.append(tt)
            self._separators.sort(cmp=TokenType.compare)
        elif isinstance(tt, Literal):
            self._literal = tt
            self._literalDelims = tt.DELIMITERS
        else:
            raise Exception('Unknown token type')

    def enableLineComments(self, lineCommentStart='//'):
        
        self._lineCommentEnabled = True
        self._lineCommentStart = lineCommentStart
           
    def enableBlockComments(self, 
                            blockCommentStart='/*', 
                            blockCommentEnd='*/'):

        self._blockCommentEnabled = True
        self._blockCommentStart = blockCommentStart
        self._blockCommentEnd = blockCommentEnd

    def getNextToken(self):

        if not self._instream:
            return None

        if self._stack:
            return self._stack.pop()
        
        consumed = ""
        startLine = 0
        startColumn = 0
        
        if not self._inputBuffer:
            self._inputBuffer = InputBuffer(self._instream, fillSize=1)
                
        while True:
            
            content = self._inputBuffer.getContent()
                        
            if not content:
                break
                        
            if not self._isTerminationString(content):
                
                ch = self._inputBuffer.consumeChar()
                curStartPos = self._updatePosInfo(ch)
                
                if self._mode == LexerMode.NORMAL:
                    if not consumed:
                        startLine = curStartPos[0]
                        startColumn = curStartPos[1]
                    consumed += ch
                
            else:

                chars = self._inputBuffer.consumeAll()
                self._updatePosInfo(chars)
                
                if self._mode == LexerMode.NORMAL:
                    
                    res = self._handleComsumption(consumed, startLine, startColumn)
                    if res:
                        return res
                    else:
                        consumed = ""
                                    
                else: # Kommentarmodus => Moduswechsel mit Content prüfen
                    
                    self._checkForModeChange(content)
                
        if consumed:
            return self._handleComsumption(consumed, startLine, startColumn)
        else:
            return None
        
    def _updatePosInfo(self, content):
        
        for i in range(len(content)):
            
            ch = content[i]
            if not ord(ch) == WSCharCode.LINEBREAK:
                self._column += 1
            else:
                self._line += 1
                self._column = 0
                
            if i == 0:
                res = (self._line, self._column)
            
        return res
        
    def _checkForModeChange(self,consumed):
        
        res = consumed
                
        if not consumed:
            return res
                
        if self._mode == LexerMode.NORMAL:
                
            if self._lineCommentEnabled and \
               self._matchesCommentBegin(consumed, self._lineCommentStart):
                
                self._mode = LexerMode.LINE_COMMENT
                self._inputBuffer = InputBuffer(self._instream,
                                                fillSize = 1 # <- Länge von '\n'
                                                )
                
                res = ""
                    
            elif self._blockCommentEnabled and \
                 self._matchesCommentBegin(consumed, self._blockCommentStart):
                
                self._mode = LexerMode.BLOCK_COMMENT
                size = len(self._blockCommentEnd);
                self._inputBuffer = InputBuffer(self._instream,
                                                fillSize = size
                                                )
                res = ""
                
        else:
            
            self._mode = LexerMode.NORMAL
            self._inputBuffer = InputBuffer(self._instream,
                                            fillSize = 1 # <- Länge aller Whitespace-Zeichen
                                            )
            res = ""
        
        return res
  
    def _getTokens(self, text, startLine, startColumn):

        # Handle literals:
        if self._literal:
            token = self._literal.createToken(text)
            if token:
                token.setStartPosition(startLine, startColumn)
                return [token]
        
        res = []

        # Find separators and split:
        for sep in self._separators:

            token = sep.createToken(text)

            if token:
                # Reihenfolge wg. POP-Logik vertauschen...
                right = sep.getRemainingRight(text)
                left = sep.getRemainingLeft(text)
                
                if right:
                    col = startColumn + len(left) + len(token.getText())
                    res = self._getTokens(right, startLine, col)
                    
                token.setStartPosition(startLine, startColumn + len(left))

                res.append(token)
                
                if left:
                    res += self._getTokens(left, startLine, startColumn)

                return res

        # Find prefixes:
        for prefix in self._prefixes:

            token = prefix.createToken(text)

            if token:

                right = prefix.getRemainingRight(text)
                if right:
                    col = startColumn + len(token.getText())
                    res = self._getTokens(right, startLine, col)
                    
                token.setStartPosition(startLine, startColumn)

                res.append(token)

                return res

        # Find postfixes:
        for postfix in self._postfixes:

            token = postfix.createToken(text)

            if token:
                
                left = postfix.getRemainingLeft(text)
                
                col = startColumn + len(left)
                token.setStartPosition(startLine, col)

                res.append(token)

                if left:
                    res += self._getTokens(left, startLine, startColumn)

                return res 

        # Find (key)words:
        
        try:
            matchingWords = [self._keywords[text]]
        except KeyError:
            # maybe case insensitive keyword?
            try:
                kw = self._keywords[text.upper()]
                if not kw.isCaseSensitive():
                    matchingWords = [kw]
                else:
                    matchingWords = []
            except KeyError:
                matchingWords = []
        
        matchingWords += [word for word in self._words if word.matches(text)]

        if matchingWords:
            token = Token(text, matchingWords)
            token.setStartPosition(startLine, startColumn)
            res.append(token)
            return res
        
        raise Exception("Unknown token '%s' at line %d, column %d" % (text, startLine, startColumn))
    
    def _handleComsumption(self, consumed, startLine, startColumn):
        
        consumed = self._checkForModeChange(consumed)
                
        if consumed:
            self._stack = self._getTokens(consumed, startLine, startColumn)
            if self._stack:
                return self._stack.pop()
            else:
                raise Exception("Unknown token '%s' at line %d, column %d" \
                                % (consumed, startLine, startColumn))
        
        return None
    
    def _isTerminationString(self, text):
        
        if self._mode == LexerMode.NORMAL:
            
            return self._isWhiteSpace(text)
        
        elif self._mode == LexerMode.LINE_COMMENT:
                
            return ord(text) == WSCharCode.LINEBREAK
        
        elif self._mode == LexerMode.BLOCK_COMMENT:
            
            return text == self._blockCommentEnd
            
        else:
            
            raise Exception("Undefined lexer mode")

    def _isWhiteSpace(self, ch):

        if ch in self._literalDelims:
            if self._currentLitDelim:
                if ch == self._currentLitDelim:
                    self._currentLitDelim = ""
            else:
                self._currentLitDelim = ch
            return False
        elif self._currentLitDelim:
            return False
        else:
            return ord(ch) in self._wsCharCodes
    
    def _matchesCommentBegin(self, consumed, commentBegin):
        
        tmp = commentBegin
        for specialChar in ['*']:
            tmp = tmp.replace(specialChar, '\\' + specialChar)
        
        regex = r"\A%s.*\Z" % tmp
        
        return bool(re.match(regex, consumed))
 
class WSCharCode:

    TAB = 9
    LINEBREAK = 10
    VTAB = 11
    FORMFEED = 12
    SPACE = 32

class LexerMode:
    
    NORMAL = 1
    LINE_COMMENT = 2
    BLOCK_COMMENT = 3
