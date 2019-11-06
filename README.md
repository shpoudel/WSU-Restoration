# WSU-Restoration

This repository contains the restoration application for IEEE 9500-node model (https://github.com/GRIDAPPSD/Powergrid-Models/tree/develop/blazegraph/test/dss/WSU). The application is hosted on GridAPPS-D platform. 

## Get network of the test case

In the optimization problem, test feeders are modeled as graph; G (V, E), where V is set of nodes and E is set of edges. The graph and line parameters of the test feeder can be extracted from (https://github.com/shpoudel/D-Net). 


## Get real-time topology and load data of the test case

First, the real time topology of the test case is extracted from the operating feeder in platform (top_identify.py). Then, load data for each node is obtained (get_Load.py) and stored in json format to be used in linear power flow while writing constraints for optimization problem.

## Isolation and Restoration

Once fault is identified in the test case, Isolation.py is invoked which isolates the fault from all possible directions. Then restoration_WSU.py solves the optimization. The output of optimization is the list of switches to toggle for reconfiguration such that load restored is maximixed. Grid-forming DERs can also be utilized to form islands if required. 
