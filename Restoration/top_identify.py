# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 11:17:12 2019

@author: spoudel
"""
import json
import networkx as nx

class Topology(object):
    """
    WSU Resilient Restoration 
    Identify the current topology of the test case
    """
    def __init__(self, msr_mrids_load, switches, sim_output, TOP, LineData, alarm, faulted):
        self.meas_load = msr_mrids_load
        self.output = sim_output
        self.switches = switches
        self.TOP = TOP
        self.LineData =  LineData
        self._alarm =  alarm
        self._faulted = faulted
        
    def curr_top(self):
        data1 = self.meas_load
        data2 = self.output
        TOP = self.TOP
        data2 = json.loads(data2.replace("\'",""))
        timestamp = data2["message"] ["timestamp"]
        meas_value = data2['message']['measurements']
        data2 = data2["message"]["measurements"]
        
        # Find interested mrids. We are only interested in Position of the switches
        ms_id = []
        bus = []
        data1 = data1['data']
        ds = [d for d in data1 if d['type'] == 'Pos']

        # Store the open switches
        Loadbreak = []
        for d1 in ds:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                p = meas_value[v]
                if p['value'] == 0:
                    Loadbreak.append(d1['eqname'])
        print('.......................................')
        print('The total number of open switches:', len(set(Loadbreak)))
        print(timestamp, set(Loadbreak))

        # Create a message dict to store the real time topology:
        message = dict (when = timestamp, op_sw = set(Loadbreak))
        TOP.append(message)

        # Flush the memory as we only need previous topology to find out the fault location
        if len(TOP) > 2:
            TOP = TOP[-2:]
        
        # print(TOP)
        # Checing if fault occured.
        # Replace this with alarm signal
        flag_event = 0
        if self._alarm == 1:
            flag_event = 1
        return TOP, flag_event, Loadbreak

    def locate_fault(self, LoadBreak):
        G = nx.Graph()
        TOP = self.TOP
        data2 = self.output
        LineData =  self.LineData
        data2 = json.loads(data2.replace("\'",""))
        timestamp = data2["message"] ["timestamp"]
        # Check with previous topology:
        for top in TOP:
            if (timestamp) == top['when']:
                curr_open = top['op_sw']
            if (timestamp - 3) == top['when']:
                previous = top['op_sw']

        op_fault  = curr_open - previous
        
        # Here I know what switches are open but need to locate fault in more generalized way..
        for l in LineData:
            if l['line'] not in previous:
                G.add_edge(l['from_br'], l['to_br'])
        T = list(nx.bfs_tree(G, source = 'SOURCEBUS').edges())

        # Finding Fault node to be used in isolation
        fault = []
        flag_fault = 0
        for l in LineData:
            if l['line'] in op_fault:
                op = [l['from_br'], l['to_br']]
                op = set(op)
                for t in T:
                    if set(t) == op:
                        fault.append(t[1])
                        flag_fault = 1
        # print (fault)
        return flag_fault, fault
        # Check for fault if topology changes and alarm is received:



    
        
