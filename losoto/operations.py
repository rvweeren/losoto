# Set of operations that LoSoTo can perform
# Each operation is a function

def reset( step, parset, H ):
   """Set specific solutions to 0 (phase, rotang) or 1 (amp)
   """
   npixels = parset.getInt('.'.join(["ExpIon.Steps", step, "npixels"]), 100 )
   extent = parset.getFloat('.'.join(["ExpIon.Steps", step, "extent"]), 0 )
   return H


def clocktec( step, parset, H ):
   """Perform clock/tec separation
   """
   raise Exception('Not yet implemented.')
   return H


def flag( step, parset, H ):
   """Flag outliers
   """
   raise Exception('Not yet implemented.')
   return H


def smooth( step, parset, H ):
   """Smooth solutions
   """
   raise Exception('Not yet implemented.')
   return H


def interp( step, parset, H ):
   """Interpolate solutions in freq/time
   """
   raise Exception('Not yet implemented.')
   return H


def plot( step, parset, H ):
   """Make some inspection plots
   """
   raise Exception('Not yet implemented.')
   return H


def apply( step, parset, H ):
   """Apply solution to a specific MS
   """
   raise Exception('Not yet implemented.')

   import numpy as np
   from pyrap.tables import table
   import _FastApply
   import numpy.linalg
   import ModColor
   import lofar.stationresponse as lsr
   import sys, os
   from progressbar import ProgressBar
   
   # parameters
   MS = parset.getString('.'.join(["LoSoTo.Steps", step, "MS"]), '' )
   doBeam = parset.getBool('.'.join(["LoSoTo.Steps", step, "Beam"]), False )
   inCol = parset.getString('.'.join(["LoSoTo.Steps", step, "InCol"]), 'DATA' )
   outCol = parset.getString('.'.join(["LoSoTo.Steps", step, "OutCol"]), 'CORRECTED_DATA' )
   Method = parset.getString('.'.join(["LoSoTo.Steps", step, "Method"]), 'RawNearest' )
   if MS == '':
       print "ERROR: no MS given, cannot correct :("
       sys.exit(1)

   t = table(MS+'/SPECTRAL_WINDOW/',ack=False)
   chan_freq = t.getcol('CHAN_FREQ')
   Freq_Mean = np.mean(chan_freq)
   t.close()

   print "Reading column %s" % inCol
   t = table(MS, ack=False)
   data = t.getcol(inCol)
   MSTime = t.getcol("TIME")
   A0 = t.getcol("ANTENNA1")
   A1 = t.getcol("ANTENNA2")
   t.close()
  
   #In [6]: H.amplitudes[:].shape
   #Out[6]: (7190, 242, 53, 1, 2, 2)

   TimeSols = H.times[:]
   FreqSols = H.freqs[:]
   SelChanSol = np.argmin(np.abs(Freq_Mean-FreqSols))
   ThisFreq = FreqSols[SelChanSol]
   K = 8.4479745e9

   if Method == "RawNearest":
       Amp = H.amplitudes[:,SelChanSol,:,0,:,:]
       Pha = H.phases[:,SelChanSol,:,0,:,:]
       SS = Amp*np.exp(1j*Pha)
   elif Method=="Clock":
       raise Exception('Not yet implemented.')
       SS = np.exp(1j*(2.*np.pi*ThisFreq*self.Clock*1e-9))
   elif Method=="ClockTEC":
       raise Exception('Not yet implemented.')
       SS = np.exp(1j*(2.*np.pi*ThisFreq*self.Clock*1e-9)+1j*self.K*self.TEC/freq)

   if ApplyBeam:
       pBAR = ProgressBar('white', block='=', empty=' ',Title="Beam Calc")
       SR = lsr.stationresponse(MS)
       for it in range(TimeSols.shape[0]):
           Beam = SR.evaluate(TimeSols[it])
           for iStation in range(SS.shape[1]):
               SS[it,iStation,:,:]=np.dot(SS[it,iStation,:,:],Beam[iStation,0,:,:])
               # SS[iStation,it,0,1]=0
               # SS[iStation,it,1,0]=0
           pBAR.render(int(100*float(it+1)/TimeSols.shape[0]), '%i/%i' % (it+1,TimeSols.shape[0]))

   DtSol = TimeSols[1]-TimeSols[0]

   data = _FastApply.FastApply(data.astype(np.complex128), MSTime, A0, A1,\
                                    SS.astype(np.complex128), np.min(TimeSols), DtSol)

   print "Writting corrected data in column %s" % outCol
   t = table(MS,ack=False,readonly=False)
   t.putcol(outCol, data)
   t.close()
   
   return H