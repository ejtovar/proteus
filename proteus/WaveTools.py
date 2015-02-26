"""Tools for working with water waves
The primary objective of this module is to provide solutions (exact and

approximate) for the free surface deformation and subsurface velocity
components of water waves. These can be used as boundary conditions,
wave generation sources, and validation solutions for numerical wave
codes.

"""
from math import pi,tanh,sqrt,exp,log,sin,cos,cosh,sinh
import numpy as np
from matplotlib  import pyplot
import Profiling as pr



def sigma(omega,omega0):
    """sigma function for JONSWAP spectrum
    """
    sigmaReturn = omega.copy()
    sigmaReturn[:] = 0.07
    sigmaReturn[omega > omega0] = 0.09
    return sigmaReturn

def JONSWAP(f,f0,Hs,g,gamma):
    """The wave spectrum from Joint North Sea Wave Observation Project

    :param f: wave frequency [1/T]
    :param f0: peak frequency [1/T]
    :param Hs: significant wave height [L]
    :param g: gravity [L/T^2]
    :param gamma: peak enhancement factor [-]
    """
    omega = 2.0*pi*f
    omega0 = 2.0*pi*f0
    alpha = 2.0*pi*0.0624*(1.094-0.01915*log(gamma))/(0.23+0.0336*gamma-0.0185/(1.9+gamma))
    r = np.exp(- (omega-omega0)**2/(2*sigma(omega,omega0)**2*omega0**2))
    return (alpha*Hs**2*omega0**4/omega**5)*np.exp(-(5.0/4.0)*(omega0/omega)**4)*gamma**r

def piersonMoskovitz(f,f0,alpha=8.1e-3,beta=0.74,g=9.8):
    """Pierson-Moskovitz spectrum

    :param f: frequency [1/T]
    :param f0: peak frequency [1/T]
    :param alpha: alpha fitting parameter [-]
    :param beta: beta fitting parameter [-]
    :param g: graivty [L/T^2]
    """
    return (5.0/16.0)*Hs**2*(f0**4/f**5)*np.exp((-5.0/4.0)*(f0/f)**4)

def dispersion(w,d, niter = 1000, g = 9.81):
    """Calculates wave vector k from linear dispersion relation

    :param w: cyclical frequency
    :param d: depth [L]
    :param niter: number  of solution iterations
    :param g: gravity [L/T^2
    """
    Kd = w*sqrt(d/g)
    for jj in range(niter):
       #Kdn_1 = Kd
        Kd = w*w*d/g/np.tanh(Kd)
        #Kdn_1 /=0.01*Kd
        #Kdn_1 -= 100.
        #Kdn_1 = abs(Kdn_1)
        #try: Kdn_1 = mean(Kdn_1)
        #except: continue
    #print "Solution convergence for dispersion relation %s percent" % Kdn_1
    return(Kd/d)

class MonochromaticWaves:
    """Generate a monochromatic wave train in the linear regime
    """
    def __init__(self,period,waveHeight,seaLevel,depth,meanVelocity,g,waveDir,wavelength=None,waveType="Linear",Ycoeff = None, Bcoeff =None, phi0 = 0.):
        self.knownWaveTypes = ["Linear","Fenton","userDefined"]
        self.waveType = waveType
        self.g = g
        self.gAbs = sqrt(sum(g * g))
        self.waveDir = waveDir/sqrt(sum(waveDir * waveDir))
        if waveType not in self.knownWaveTypes:
            pr.logEvent("Wrong wavetype given: Valid wavetypes are %s") %(self.knownWaveTypes)
        dircheck = abs(sum(g * waveDir))
        if dircheck > 1e-6:
            pr.logEvent("Wave direction is not perpendicular to gravity vector. Check input")
            exit(1)
        self.period = period
        self.waveHeight = waveHeight
        self.seaLevel = seaLevel
        self.depth = depth
        self.omega = 2.0*pi/period
        if  self.waveType is "Linear":
            self.k = dispersion(w=self.omega,d=self.depth,g=self.gAbs)
            self.wavelength = 2.0*pi/self.k
        else:
            try:
                self.k = 2.0*pi/wavelength
                self.wavelength=wavelength
            except:
                pr.logEvent("Wavelenght is not defined for nonlinear waves. Enter wavelength in class arguments")  
        self.kDir = self.k * self.waveDir 
        self.amplitude = 0.5*self.waveHeight
        self.meanVelocity = meanVelocity
        self.vDir = self.g/self.gAbs
        if (Ycoeff is None) or (Bcoeff is None):
            if self.waveType is not "Linear":
                pr.logEvent("Need to define Ycoeff and Bcoeff (free-surface and velocity) for nonlinear waves")                          
    def phase(self,x,y,z,t):        
        return x*self.kDir[0]+y*self.kDir[1]+z*self.kDir[2] - self.omega*t
#    def theta(self,x,t):
#        return self.k*x - self.omega*t + pi/2.0
#    def Z(self,z):
#        return z - self.seaLevel
    def eta(self,x,y,z,t):
        if self.waveType is linear:
            return self.amplitude*cos(self.phase(x,y,z,t))
        else:
            HH = 0.
            ii =0.
            for Y in self.YCoeff:
                ii+=1
                HH+=Y*cos(ii*self.phase(x,y,z,t))
            if self.waveType is "Fenton": return HH/self.k
            else: return HH
    def Z(self,x,y,z,t):
        return   -(self.vDir[0]*x + self.vDir[1]*y+ self.vDir[2]*z) - self.seaLevel
    def UH(self,x,y,z,t):
        if(self.waveType is "Linear"):
            return self.amplitude*self.omega*cosh(self.k*(self.Z(x,y,z)+self.depth))*cos(self.phase(x,y,z,t))/sinh(self.k*self.depth)
        else:
            UH = 0.
            ii=0.
            for B in self.Bcoeff:
                ii+=1.
                UH_t =B*cosh(self.k*(self.Z(x,y,z)+self.depth))*cos(self.phase(x,y,z,t))/cosh(self.k*self.depth)
                if waveType is "Fenton":
                    UH+=ii*UH_t
                else:
                    UH+=UH_t
                    
    def UV(self,x,y,z,t):
        if waveType is "Linear":
            return self.sigma*self.amplitude*sinh(self.k*(self.Z(x,y,z)+self.depth))*sin(self.theta(x,y,z,t))/sinh(self.k*self.depth)
        else:
            UV = 0.
            ii=0.
            for B in self.Bcoeff:
                ii+=1.
                UH_t =B*sinh(self.k*(self.Z(x,y,z)+self.depth))*sin(self.phase(x,y,z,t))/cosh(self.k*self.depth)
                if waveType is "Fenton":
                    UH+=ii*UH_t
                else:
                    UH+=UH_t
                    
    def uvector(x,y,z,t):
        return self.waveDir*self.UH(x,y,z,t) - self.vDir * self.UV(x,y,z,t) 
    def u(x,y,z,t):
        utemp =self.uvector(x,y,z,t)
        return utemp[0]
    def v(x,y,z,t):
        utemp =self.uvector(x,y,z,t)
        return utemp[1]
    def w(x,y,z,t):
        utemp =self.uvector(x,y,z,t)
        return utemp[2]

'''
class RandomWaves:
    """Generate approximate random wave solutions

    :param Tp: peak period [T]
    :param Hs: significant wave height [L]
    :param  d: depth [L]
    :param fp: frequency [1/T]
    :param bandFactor: width factor for band  around fp [-]
    :param N: number of frequency bins [-]
    :param mwl: mean water level [L]"""
    
    def __init__(self,
                 Tp = 5.0,         #s peak period
                 Hs = 2.0,         #m significant wave height
                 d = 2.0,           #m depth
                 fp = 1.0/5.0,      #peak  frequency
                 bandFactor = 2.0, #controls width of band  around fp
                 N = 101,          #number of frequency bins
                 mwl = 0.0,        #mean water level
                 g = 9.81,         #accelerationof gravity
                 spec_fun = JONSWAP): #wave spectrum
        self.Tp = Tp
        self.Hs = Hs
        self.d = d
        self.fp = fp
        self.bandFactor = bandFactor
        self.N = N
        self.mwl = mwl
        self.g = g
        self.fmax = self.bandFactor*self.fp
        self.fmin = self.fp/self.bandFactor
        self.df = (self.fmax-self.fmin)/float(self.N-1)
        self.fi=np.zeros(self.N,'d')
        for i in range(self.N):
            self.fi[i] = self.fmin+self.df*i
        self.ki = dispersion(2.0*pi*self.fi,self.d,g=self.g)
        self.phi = 2.0*pi*np.random.random(self.fi.shape[0])
        #ai = np.sqrt((Si_J[1:]+Si_J[:-1])*(fi[1:]-fi[:-1]))
        fim_tmp = (0.5*(self.fi[1:]+self.fi[:-1])).tolist()
        self.fim = np.array([fim_tmp[0]-0.5*self.df]+fim_tmp+[fim_tmp[-1]+0.5*self.df])
        self.Si_Jm = spec_fun(self.fim,f0=self.fp,Hs=self.Hs,g=self.g,gamma=3.3)
        self.ai = np.sqrt((self.Si_Jm[1:]+self.Si_Jm[:-1])*(self.fim[1:]-self.fim[:-1]))
    
    def eta(self,x,t):
        """Free surface displacement
        
        :param x: floating point x coordinate
        :param t: time"""
        return (self.ai*np.cos(2.0*pi*self.fi*t - self.ki*x + self.phi)).sum()
    
    def u(self,x,z,t):
        """x-component of velocity

        :param x: floating point x coordinate
        :param z: floating point z coordinate (height above bottom)
        :param t: time
        """
        Z = z - self.mwl
        return (2.0*pi*self.fi*self.ai*np.cos(2.0*pi*self.fi*t-self.ki*x+self.phi)*
                np.cosh(self.ki*(self.d+Z))/np.sinh(self.ki*self.d)).sum()
    
    def w(self,x,z,t):
        """z-component of velocity
        
        :param x: floating point x coordinate
        :param z: floating point z coordinate (height above bottom)
        :param t: time"""
        Z = z - self.mwl
        return (2.0*pi*self.fi*self.ai*np.sin(2.0*pi*self.fi*t-self.ki*x+self.phi)*
                np.sinh(self.ki*(self.d+Z))/np.sinh(self.ki*self.d)).sum()

if __name__ == '__main__':
    Tp = 5.0 #s peak period
    Hs = 2.0 #m significant wave height
    d = Hs #m depth
    fp = 1.0/Tp #peak  frequency
    bandFactor = 2.0 #controls width of band  around fp
    N = 101 # number of frequency bins
    mwl = 0.0 #mean water level    Hs = 2.0
    waves = RandomWaves(Tp = Tp,
                        Hs = Hs,
                        d = d,
                        fp = fp,
                        bandFactor = bandFactor,
                        N = N,
                        mwl = mwl,
                        g = 9.81)
    waves = RandomWaves(Tp = 1.94,
                        Hs = 0.1,
                        d  = 1.0,
                        fp = 1.0/1.94,
                        bandFactor = 2.0,
                        N = 101,
                        mwl = 1.0,
                        g = 9.8)#shouldn't mwl = d always?
    waves = MonochromaticWaves(period=1.94,
                              waveHeight=0.1,
                              seaLevel = 1.0,
                              depth = 1.0,
                              meanVelocity=0.0,
                              g=np.array([0,-9.81,0]),
                               waveDir = np.array([1,0,0])
                               )
    fp = 1.0/1.94
    d = 1.0
    Hs = 0.1
    Tp = 1.94
    
    kp = dispersion(2.0*pi*fp,d)
    nn = 51
    zmax = d+1.8*Hs/2.0
    xmax = 10*zmax
    T=0.0
    L = 6.0*pi/kp
    T_end = 10.0*Tp
    nt = 10*2#21
    x = np.linspace(0,xmax,nn)
    z = np.linspace(0,zmax,nn)
    X,Z = np.meshgrid(x,z)
    U = np.zeros((nn,nn),'d')
    W = np.zeros((nn,nn),'d')
    for n,T in enumerate(np.linspace(0,T_end,nt)):
        for J,xi in enumerate(x):
            for I,zi in enumerate(z):
                z_surf = d+waves.eta(xi,T)
                if zi < z_surf:
                    UIJ = waves.u(xi,zi,T)
                    WIJ = waves.w(xi,zi,T)
                    U[I,J] =  UIJ
                    W[I,J] = WIJ
                else:
                    U[I,J] = 0.0
                    W[I,J] = 0.0
        speed = np.sqrt(U*U + W*W)
        hl = [d+waves.eta(xi,T) for xi in x]
        pyplot.clf()
        #pyplot.axis('equal')
        pyplot.plot(x,hl)
        pyplot.streamplot(x, z, U, W,density=(1,1), color=speed,linewidth=2.5*speed/speed.max())
        #pyplot.contourf(x,z,speed)
        fig = pyplot.gcf()
        fig.set_size_inches(16.0,16.0*zmax/xmax)
        pyplot.savefig('frame%4.4d.png' % n)
    
'''
