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

class InputBuffer(object):
    
    def __init__(self, stream, fillSize=1):
        
        self._stream = stream
        self._fillSize = fillSize
        self._content = ""
    
    def getContent(self):
        
        self._fillContent()
        
        return self._content
                
    def consumeChar(self):
        
        res = ''
        
        if len(self._content):
            
            res = self._content[0]
            self._content = self._content[1:]
            self._fillContent()
        
        return res
        
    def consumeAll(self):
                
        res = self._content
        self._content = ""
        
        return res
        
    def _fillContent(self):
        
        while len(self._content) < self._fillSize:
            if self._stream.endOfInput():
                break
            self._content += self._stream.getNextChar()
