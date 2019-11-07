# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 11:17:12 2019

@author: spoudel
"""
import json
import numpy as np
import math

class PowerData(object):
    """
    WSU Resilient Restoration
    """
    def __init__(self, msr_mrids_load, sim_output):
        self.meas_load = msr_mrids_load
        self.output = sim_output
        
    def demand(self):
        data1 = self.meas_load
        data2 = self.output
        data2 = json.loads(data2.replace("\'",""))
        data2 = data2['message']['measurements']     

        # Find interested mrids of 9500 Node. We are only interested in VA of the nodes
        # Convert VA to kw and kVAR
        Demand = []
        s = 0.
        for d1 in data1['data']: 
            if d1['type'] == 'VA':                
                for n, pq in data2.items():
                    if n == d1['measid']:
                        # Check phase of load in 9500 node based on last letter
                        loadbus = d1['bus']
                        phase = loadbus[-1].upper()
                        phi = (pq['angle'])*math.pi/180
                        message = dict(bus = d1['bus'],
                                       VA = [pq['magnitude'], pq['angle']],
                                       Phase = phase,
                                       kW = 0.001 * pq['magnitude']*np.cos(phi),
                                       kVaR = 0.001* pq['magnitude']*np.sin(phi))
                        Demand.append(message)     
                        break  
        for d in Demand:
            s += d['kW']
        print('Total demand:', s)

        with open('PlatformD.json', 'w') as json_file:
            json.dump(Demand, json_file)

        # Transferring the load to Primary side for solving the restoration. No triplex line in optimization model


    
        
