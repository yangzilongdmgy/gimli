#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygimli as pg
import pybert as pb
import numpy as np

def createCacheName(base, mesh=None):
    nc = ''
    if mesh:
        nc = str(mesh.nodeCount())
    return 'cache-' + base + "-" + nc

def resistivityArchie(rBrine, porosity, a=1.0, m=2.0, S=1.0, n=2.0,
                      mesh=None, meshI=None):
    """
    .. math:: 
        \rho = a\rho_{\text{Brine}}\phi^{-m}\S_w^{-n}
        
    * :math:`\rho` - the electrical conductivity of the fluid saturated rock
    * :math:`\rho_{\text{Brine}}` - electrical conductivity of the brine
    * :math:`\phi` - porosity 0.0 --1.0
    * :math:`a` - tortuosity factor. (common 1)
    * :math:`m` - cementation exponent of the rock
            (usually in the range 1.3 -- 2.5 for sandstones)
    * :math:`n` - is the saturation exponent (usually close to 2)
     
    """
    rB = None
    
    if rBrine.ndim == 1:
        rB = pg.RMatrix(1, len(rBrine))
        rB[0] = parseArgToArray(rBrine, mesh.cellCount(), mesh)
    elif rBrine.ndim == 2:
        rB = pg.RMatrix(len(rBrine), len(rBrine[0]))
        for i in range(len(rBrine)):
            rB[i] = rBrine[i]
     
    porosity = pg.solver.parseArgToArray(porosity, mesh.cellCount(), mesh)
    a = pg.solver.parseArgToArray(a, mesh.cellCount(), mesh)
    m = pg.solver.parseArgToArray(m, mesh.cellCount(), mesh)
    S = pg.solver.parseArgToArray(S, mesh.cellCount(), mesh)
    n = pg.solver.parseArgToArray(n, mesh.cellCount(), mesh)
    
    r = pg.RMatrix(len(rBrine), len(rBrine[0]))
    for i in range(len(r)):
        r[i] = rB[i] * a * porosity**(-m) * S**(-n)
            
    rI = pg.RMatrix(len(r), meshI.cellCount())
    if meshI:
        pg.interpolate(mesh, r, meshI.cellCenters(), rI) 
        
    for i in range(len(rI)):
        rI[i] = pg.solver.fillEmptyToCellArray(meshI, rI[i])
        
    rI.round(1e-6)
    #print(rI)
    return rI


def simulateERTData(saturation, meshSat, cache=False, i=-1, j=0, verbose=0):
    swatch = pg.Stopwatch(True)
    #ertScheme = pb.DataContainerERT('20dd.shm')
    
    ertScheme = pb.createData(np.arange(-5, 15.001, 1), schemeName='dd')
        
    meshERT = pg.meshtools.createParaMesh(ertScheme, quality=34,
                                          paraMaxCellSize=0.1, 
                                          boundaryMaxCellSize=10)
    
    
    #pg.show(meshSat, meshSat.cellMarker())
    #pg.wait()
    conductivityBack = 1./100#np.array([1./4, 1./100, 1./10])[meshSat.cellMarker()]
    
    #1./10.
    conductivityBrine = 10.
    conductivity = saturation * conductivityBrine + (1. - saturation) * conductivityBack
    
    resis = resistivityArchie(rBrine=1./conductivity,
                              porosity=0.3, S=1.0, 
                              mesh=meshSat, meshI=meshERT)

    #pg.show(meshERT, resis[-1], colorBar=1)
    #pg.wait()
    
    ert = pb.manager.Resistivity(verbose=False)
    
    #if i > 0:
        ##np.save('resis' + str(i) + '-' + str(j), resis)
        #rt = np.load('resis' + str(i) + '-' + str(j) + ".npy")
        #print("rt:", i, j, np.sum(rt-resis))
        #np.testing.assert_array_equal(resis, rt)
        
    rhoa = ert.simulate(meshERT, resis, ertScheme, verbose=0)
    
    np.round(rhoa)
    
    ertScheme.set('k', pb.geometricFactor(ertScheme))
    
    errPerc = 1.
    errVolt = 1e-5
    voltage = rhoa / ertScheme('k')
    err = np.abs(errVolt / voltage) + errPerc / 100.0

    if verbose:
        print('err min:', min(err)*100, 'max:', max(err)*100)
    
    dRhoa = rhoa[1:]/rhoa[0]
    dErr = err[1:]
    return meshERT, ertScheme, resis, dRhoa, dErr


def showERTData(scheme, rhoa, axes):
    s = pb.DataContainerERT(scheme)
    s1 = pb.DataContainerERT(scheme)
    
    print(rhoa.shape)
    for i in range(1, len(rhoa)):
        s1.translate([float(scheme.sensorCount()+1), 0])
        s.add(s1)
    
    #s.save('s.shm')
    pb.showData(s, vals=rhoa.flatten(), schemeName='dd', colorBar=1, axes=axes)
    

if __name__ == '__main__':
    pass
pg.wait()

