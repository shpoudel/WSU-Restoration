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
    WSU Resilient Restoration, Get load data from feeder
    """
    def __init__(self, msr_mrids_load, sim_output, xfmr, inverters, ders, sub, store):
        self.meas_load = msr_mrids_load
        self.output = sim_output
        self.xfmr = xfmr
        self.inverters = inverters
        self.ders = ders
        self.sub = sub
        self.store = store
        
    def demand(self):
        data1 = self.meas_load
        data2 = self.output
        # data2 = json.loads(data2.replace("\'",""))
        meas_value = data2['message']['measurements']     
        timestamp = data2["message"] ["timestamp"]

        # Find interested mrids of 9500 Node. We are only interested in VA of the nodes
        # Convert VA to kw and kVAR        
        data1 = data1['data']
        ds = [d for d in data1 if d['type'] != 'PNV']

        Demand = []
        for d1 in ds:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                pq = meas_value[v]
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

        # Combine the dictionary from S1 and S2 to balanced load. 
        # VA measumrement has two different loads on S1 and S2 phase
        for i, l in enumerate(Demand):
            if i % 2 == 0:
                d1 = Demand[i]
                d2 = Demand[i+1]
                l['kW'] = d1['kW'] + d2['kW']
                l['kVaR'] = d1['kVaR'] + d2['kVaR']
        
        Demand = [l for d, l in enumerate(Demand) if d % 2 == 0]

        for ld in Demand:
            node = ld['bus'].strip('s')
            # Find this node in Xfrm to_br
            for tr in self.xfmr:
                sec = tr['bus2']
                if sec == node:
                    # Transfer this load to primary and change the node name
                    ld['bus'] = tr['bus1'].upper()

        sP = 0
        sQ = 0
        sNN_P = 0
        sNN_Q = 0
        for d in Demand:
            sP += d['kW']
            sQ += d['kVaR']
            if 'M200' in d['bus']:
                sNN_P += d['kW']   
                sNN_Q += d['kVaR']   
        
        # If platform gave random load for New neighborhood, then use the static loads
        if sNN_P == 0:
            sNN_P = 1121.6
            sNN_Q = 635.64

        print('The total real and reactive demand is:', sP, sQ, sNN_P, sNN_Q)
        print('.....................................................')
        print('\n')   
        return Demand, sNN_P, sNN_Q

    def pvinv(self):

        data1 = self.inverters
        data2 = self.output
        # data2 = json.loads(data2.replace("\'",""))
        meas_value = data2['message']['measurements']     
        timestamp = data2["message"] ["timestamp"]

        # Find interested mrids of 9500 Node. We are only interested in VA of the nodes
        # First, we deal with only PV in new neighborhood so bus name to be sx200 
        data1 = data1['data']
        ds = [d for d in data1 if d['type'] != 'PNV' and 'sx200' in d['bus']]
        pv_out = []
        for d1 in ds:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                pq = meas_value[v]
                # Check phase of load in 9500 node based on last letter
                loadbus = d1['bus']
                phase = loadbus[-1].upper()
                phi = (pq['angle'])*math.pi/180
                message = dict(bus = d1['bus'],
                                VA = [pq['magnitude'], pq['angle']],
                                Phase = phase,
                                kW = 0.001 * pq['magnitude']*np.cos(phi),
                                kVaR = 0.001* pq['magnitude']*np.sin(phi))
                pv_out.append(message)    

        # Combine the dictionary from S1 and S2 to balanced load. 
        # VA measumrement has two different loads on S1 and S2 phase
        for i, l in enumerate(pv_out):
            if i % 2 == 0:
                d1 = pv_out[i]
                d2 = pv_out[i+1]
                l['kW'] = d1['kW'] + d2['kW']
                l['kVaR'] = d1['kVaR'] + d2['kVaR']
        pv_out = [l for d, l in enumerate(pv_out) if d % 2 == 0]

        # Find interested mrids of 9500 Node. We are only interested in VA of the nodes
        # First, we deal with only inverter based DER in new neighborhood so bus name is m2001
        ds = [d for d in data1 if d['type'] != 'PNV' and 'm2001' in d['bus']]
        ess_out = []
        for d1 in ds:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                pq = meas_value[v]
                loadbus = d1['bus']
                phase = d1['phases']
                phi = (pq['angle'])*math.pi/180
                message = dict(bus = d1['bus'],
                                VA = [pq['magnitude'], pq['angle']],
                                Phase = phase,
                                kW = 0.001 * pq['magnitude']*np.cos(phi),
                                kVaR = 0.001* pq['magnitude']*np.sin(phi))
                ess_out.append(message)    

        # Combining phase A, B, and C
        for i, l in enumerate(ess_out):
            if i % 3 == 0:
                d1 = ess_out[i]
                d2 = ess_out[i+1]
                d3 = ess_out[i+2]
                l['kW'] = d1['kW'] + d2['kW'] + d3['kW']
                l['kVaR'] = d1['kVaR'] + d2['kVaR'] +d3['kVaR']
        ess_out = [l for d, l in enumerate(ess_out) if d % 3 == 0]

        print('--------------------------------')
        print('ESS_bus', '\t', 'Output', '\n')
        for e in ess_out:            
            print(e['bus'], '\t', e['kW'], '\n')
        # print(ess_out)
        return pv_out

    
    def DER_dispatch(self):

        data1 = self.ders
        data2 = self.output
        meas_value = data2['message']['measurements']     
        timestamp = data2["message"] ["timestamp"]
        der_out = []
        for d1 in data1:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                pq = meas_value[v]
                loadbus = d1['bus']
                phase = d1['phases']
                phi = (pq['angle'])*math.pi/180
                message = dict(line = d1['eqname'],
                                bus = d1['bus'],
                                VA = [pq['magnitude'], pq['angle']],
                                Phase = phase,
                                kW = 0.001 * pq['magnitude']*np.cos(phi),
                                kVaR = 0.001* pq['magnitude']*np.sin(phi))
                der_out.append(message)   

        # Combining phase A, B, and C
        for i, l in enumerate(der_out):
            if i % 3 == 0:
                d1 = der_out[i]
                d2 = der_out[i+1]
                d3 = der_out[i+2]
                l['kW'] = d1['kW'] + d2['kW'] + d3['kW']
                l['kVaR'] = d1['kVaR'] + d2['kVaR'] + d3['kVaR']
        der_out = [l for d, l in enumerate(der_out) if d % 3 == 0]

        print('**********************************************************************')
        print('DER_LINE','\t', 'DER_bus', '\t', 'Output', '\n')
        for d in der_out:            
            print(d['line'], '\t', d['bus'], '\t', d['kW'], '\n')
        # Display output of DERs in table format
        print('**********************************************************************')
        return der_out


    def Sub_Power(self):
        data1 = self.sub
        data2 = self.output
        meas_value = data2['message']['measurements']     
        timestamp = data2["message"] ["timestamp"]
        der_out = []
        for d1 in data1:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                pq = meas_value[v]
                loadbus = d1['bus']
                phase = d1['phases']
                phi = (pq['angle'])*math.pi/180
                message = dict(tim = timestamp,
                                line = d1['eqname'],
                                VA = [pq['magnitude'], pq['angle']],
                                Phase = phase,
                                kW = 0.001 * pq['magnitude']*np.cos(phi),
                                kVaR = 0.001* pq['magnitude']*np.sin(phi))
                der_out.append(message)   
                self.store.append(message)
        
        # with open('SubPower.json', 'w') as fp:
        #     json.dump(self.store, fp)

        return self.store
