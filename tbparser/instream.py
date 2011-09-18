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

class InStream(object):
    
    def __init__(self):
        pass
    
    def getNextChar(self):
        return ''
    
    def endOfInput(self):
        return True

class StringInput(InStream):

    def __init__(self, text):
        
        InStream.__init__(self)

        self._text = text
        self._idx = 0

    def getNextChar(self):

        if not self.endOfInput():
            res = self._text[self._idx]
            self._idx += 1
            return res
        else:
            return ''
    
    def endOfInput(self):
        
        return self._idx >= len(self._text)

class FileInput(InStream):

    def  __init__(self, filePath):
        
        InStream.__init__(self)
        
        self._filePath = filePath
        self._lines = None
        
    def endOfInput(self):

        if self._lines is None:
            self._read()
        
        if self._curLineNum >= len(self._lines):
            return True
        else:
            line = self._lines[self._curLineNum]
            return self._curColumn >= len(line)
                
    def getNextChar(self):
        
        if self._lines is None:
            self._read()
     
        if not self.endOfInput():
            line = self._lines[self._curLineNum]
            res = line[self._curColumn]
            self._next()
            return res
        else:
            return ''
        
    def _next(self):
        
        line = self._lines[self._curLineNum]
        self._curColumn += 1
        if self._curColumn >= len(line):
            self._curLineNum += 1
            self._curColumn = 0
        
    def _read(self):
        
        f = open(self._filePath, "r")
        self._lines = f.readlines()
        f.close()
        self._curLineNum = 0
        self._curColumn = 0
