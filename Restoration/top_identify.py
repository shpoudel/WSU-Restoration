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
    def __init__(self, msr_mrids_load, switches, sim_output, TOP, LineData):
        self.meas_load = msr_mrids_load
        self.output = sim_output
        self.switches = switches
        self.TOP = TOP
        self.LineData =  LineData
        
    def curr_top(self):
        data1 = self.meas_load
        data2 = self.output
        TOP = self.TOP
        data2 = json.loads(data2.replace("\'",""))
        timestamp = data2["message"] ["timestamp"]
        data2 = data2["message"]["measurements"]
        
        # Find interested mrids. We are only interested in Position of the switches
        ms_id = []
        bus = []
        for d1 in data1['data']: 
            if d1['type'] == "Pos":
                ms_id.append(d1['measid'])

        # Store the open switches
        store = []
        opens = []
        for k, v in data2.items():
            if (v['measurement_mrid']) in ms_id:
                if v['value'] == 0:
                    opens.append(v['measurement_mrid'])

        Loadbreak = []
        for d1 in data1['data']: 
            if d1['measid'] in opens:
                Loadbreak.append(d1['eqname'])

        print('The total number of open switches:', len(set(Loadbreak)))
        # print(timestamp, set(Loadbreak))

        # Create a message dict to store the real time topology:
        message = dict (when = timestamp, op_sw = set(Loadbreak))
        TOP.append(message)
        nor_open = ['ln0653457_sw','v7173_48332_sw', 'tsw803273_sw', 'a333_48332_sw','tsw320328_sw',\
                   'a8645_48332_sw','tsw568613_sw']
        # print(TOP)
        flag_event = 0
        if set(Loadbreak) != set(nor_open):
            flag_event = 1
            print('\n')
            print ('Fault has occured!!!!!!')
        return TOP, flag_event

    def locate_fault(self):
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
        nor_open = ['ln0653457_sw','v7173_48332_sw', 'tsw803273_sw', 'a333_48332_sw','tsw320328_sw',\
                   'a8645_48332_sw','tsw568613_sw', 'wf856_48332_sw', 'wg127_48332_sw']  
        for l in LineData:
            if l['line'] not in nor_open:
                G.add_edge(l['from_br'], l['to_br'])
        T = list(nx.bfs_tree(G, source = 'SOURCEBUS').edges())

        # Finding Fault node to be used in isolation
        node = []
        for l in LineData:
            if l['line'] in op_fault:
                node.append(l['index'])        
        fault = []
        for n in node:
            a = T[n]
            fault.append(a[1])
        flag_fault = 1
        return flag_fault, fault
        # Check for fault if topology changes and alarm is received:



    
        
