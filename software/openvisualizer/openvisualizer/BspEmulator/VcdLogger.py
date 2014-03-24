import os
import threading

class VcdLogger(object):
    
    ACTIVITY_DUR = 1000 # 1000ns=1us
    
    #======================== singleton pattern ===============================
    
    _instance = None
    _init     = False
    
    SIGNAMES  = ['frame','slot','fsm','task','isr','radio','ka','syncPacket','syncAck','debug']
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VcdLogger, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    #======================== main ============================================
    
    def __init__(self):
        
        # don't re-initialize an instance (singleton pattern)
        if self._init:
            return
        self._init = True
        
        # local variables
        self.f          = open('debugpins_0.vcd','w')
        self.signame    = {}
        self.lastTs     = {}
        self.dataLock   = threading.Lock()
        self.enabled    = False
        self.sigChar    = ord('!')
        self.moteIndex  = 0
        
        # create header
        header  = []
        header += ['$timescale 1ns $end\n']
        header += ['$scope module logic $end\n']
        header += ['$upscope $end\n']
        header += ['$enddefinitions $end\n']
        header  = ''.join(header)
        
        # write header
        self.f.write(header) 

    def addMoteDefinitions(self):
        
        # close previous file first        
        self.f.close()
        previousFile  = open('debugpins_'+str(self.moteIndex)+'.vcd','r')
        self.f        = open('debugpins_'+str(self.moteIndex + 1)+'.vcd','w') # use this file to insert mote definitions

        string  = previousFile.readline()
        while (string != ''):
            if string == '$upscope $end\n':
                for signal in self.SIGNAMES:
                    self.signame[(self.moteIndex + 1,signal)] = chr(self.sigChar)
                    self.f.write(
                        '$var wire 1 {0} {1}_{2} $end\n'.format(
                            chr(self.sigChar),
                            self.moteIndex + 1,
                            signal,
                        )
                    )
                    self.sigChar += 1
            self.f.write(string)
            string = previousFile.readline()
        # write the end
        previousFile.close()

        os.remove('debugpins_'+str(self.moteIndex)+'.vcd')

        # increase mote index
        self.moteIndex  += 1
            
    def setEnabled(self,enabled):
        assert enabled in [True,False]
        
        with self.dataLock:
            self.enabled = enabled
    
    def log(self,ts,mote,signal,state):
        
        assert signal in self.SIGNAMES
        assert state in [True,False]
        
        # stop here if not enables
        with self.dataLock:
            if not self.enabled:
                return
        
        # translate state to val
        if state:
            val = 1
        else:
            val = 0
        
        with self.dataLock:
            # format
            output  = []
            tsTemp = int(ts*1000000)*1000
            if ((mote,signal) in self.lastTs) and self.lastTs[(mote,signal)]==ts:
                tsTemp += self.ACTIVITY_DUR
            output += ['#{0}\n'.format(tsTemp)]
            output += ['{0}{1}\n'.format(val,self.signame[(mote,signal)])]
            output  = ''.join(output)
            
            # write
            self.f.write(output)
            
            # remember ts
            self.lastTs[(mote,signal)] = ts
        