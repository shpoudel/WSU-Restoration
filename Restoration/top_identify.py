# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 11:17:12 2019

@author: spoudel
"""
import json
import networkx as nx

class Topology(object):
    """
    A topology process class
    Identify the current topology of the test case and locate the fault if alarm is received
    Also gives the spanning tree at each time step if called upon. 
    """

    def __init__(self, msr_mrids_sw, switches, sim_output, TOP, un_graph, alarm, faulted):
        """ 
        Parameters
        ----------
        msr_mrids_sw: list(dict)
            The measurement mrids of switches for getting the real time status
        switches: list(dict)
            Object mrids for switches to control their status
        TOP: list(dict)
            A virtual memory for fault location
        un_graph: list(dict)
            A list containing the graph information of 9500 node model
        alarm: (0/1)
            A binary number indicating the fault. Relates to alarm service in main.py
        faulted: list(dict)
            A list of switches that are tripped by testmanager
        """

        self.msr_mrids_sw = msr_mrids_sw
        self.output = sim_output
        self.switches = switches
        self.TOP = TOP
        self.un_graph =  un_graph
        self._alarm =  alarm
        self._faulted = faulted     
        
    def curr_top(self):
        msr_mrids_sw = self.msr_mrids_sw
        data2 = self.output     
        TOP = self.TOP
        timestamp = data2["message"] ["timestamp"]
        meas_value = data2['message']['measurements']
        
        # Find interested mrids. We are only interested in Pos of the switches
        ms_id = []
        bus = []     
        data1 = msr_mrids_sw['data']
        ds = [d for d in data1 if d['type'] == 'Pos']

        # Store the open switches
        Loadbreak = []
        for d1 in ds:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                p = meas_value[v]
                if p['value'] == 0:
                    Loadbreak.append(d1['eqname'])

        print('.....................................................')
        print('The total number of open switches:', len(set(Loadbreak)))
        print(timestamp, set(Loadbreak))

        # Is New neighborhood islanded, if yes, then dispatch the signal to support the island
        dispatch = 0
        if 'ln2000001_sw' in Loadbreak:
            dispatch = 1

        # Create a message dict to store the real time topology:
        message = dict (when = timestamp, op_sw = set(Loadbreak))
        TOP.append(message)

        # Flush the memory as we only need previous topology to find out the fault location
        if len(TOP) > 5:
            TOP = TOP[-5:]
        
        # Checing if there is alarm and then raise the flag for event
        flag_event = 0
        if self._alarm == 1:
            flag_event = 1
        return TOP, flag_event, Loadbreak, dispatch

    def locate_fault(self):
        
        G = nx.Graph()
        TOP = self.TOP
        meas_value = self.output
        timestamp = meas_value["message"] ["timestamp"]

        # Check with previous topology to find what switch was tripped because of fault:
        for top in TOP:
            if (timestamp) == top['when']:
                curr_open = top['op_sw']
            if (timestamp - 6) == top['when']:
                previous = top['op_sw']
        op_fault  = curr_open - previous

        # Removing the isolating for DER switch as they are opened for complaince with IEEE 1547 standard
        der_sw = ['ln5001chp_sw', 'ln1047pvfrm_sw', 'dg1089dies_sw','dg1089lng_sw', 'dg1142lng_sw', 'dg1209dies_sw']
        op_fault = [trip for trip in op_fault if trip not in der_sw]
        
        # Here we know what switches are tripped but need to locate fault in more generalized way
        for l in self.un_graph:
            if l['name'] not in previous:
                G.add_edge(l['bus1'], l['bus2'])
        T = list(nx.bfs_tree(G, source = 'sourcebus').edges())

        # Finding Fault node to be used in isolation
        fault = []
        flag_fault = 0
        for l in self.un_graph:
            if l['name'] in op_fault:
                op = [l['bus1'], l['bus2']]
                op = set(op)
                for t in T:
                    if set(t) == op:
                        fault.append(t[1])
                        flag_fault = 1
        return flag_fault, fault
    
    def spanning_tree(self):

        G = nx.Graph()
        msr_mrids_sw = self.msr_mrids_sw
        sim_output = self.output     
        timestamp = sim_output["message"] ["timestamp"]
        meas_value = sim_output['message']['measurements']
        
        # Find interested mrids. We are only interested in Pos of the switches
        ms_id = []
        bus = []     
        data1 = msr_mrids_sw['data']
        ds = [d for d in data1 if d['type'] == 'Pos']

        # Store the open switches
        Loadbreak = []
        for d1 in ds:                
            if d1['measid'] in meas_value:
                v = d1['measid']
                p = meas_value[v]
                if p['value'] == 0:
                    Loadbreak.append(d1['eqname'])
        
        for l in self.un_graph:
            if l['name'] not in Loadbreak:
                G.add_edge(l['bus1'], l['bus2'])
        T = list(nx.bfs_tree(G, source = 'sourcebus').edges())
        print("\n Number of Nodes:", G.number_of_nodes(), "\n", "Number of Edges:", G.number_of_edges())
        print('\n The number of edges in a Spanning tree is:', len(T))


        



    
        
