# WSU-Restoration Application

This repository contains the restoration application for IEEE 9500-node model (https://github.com/GRIDAPPSD/Powergrid-Models/tree/develop/blazegraph/test/dss/WSU). The application is hosted on GridAPPS-D platform. 

## Get network of the test case

In the optimization problem, test feeders are modeled as graph; G (V, E), where V is set of nodes and E is set of edges. The graph and line parameters of the test feeder can be extracted from (https://github.com/shpoudel/D-Net). 


## Get real-time topology and load data of the test case

First, the real time topology of the test case is extracted from the operating feeder in platform (top_identify.py). Then, load data for each node is obtained (get_Load.py) and stored in json format to be used in linear power flow while writing constraints for optimization problem.

## Isolation and Restoration

Once fault is identified in the test case, Isolation.py is invoked which isolates the fault from all possible directions. Then restoration_WSU.py solves the optimization. The output of optimization is the list of switches to toggle for reconfiguration such that load restored is maximixed. Grid-forming DERs can also be utilized to form islands if required. 

## Quick Start

The following procedure will use the already existing containers for the gridappsd sample application.

1. Clone the gridappsd-docker repository
    ```console
    git clone https://github.com/GRIDAPPSD/gridappsd-docker
    cd gridappsd-docker
    ```
1. Run the docker containers
    ```console
    ./run.sh
    ```
1. Once inside the container start gridappsd
    ```console
    ./run-gridappsd.sh
    ```
    
1. Open browser to http://localhost:8080 (follow instructions https://gridappsd.readthedocs.io/en/latest/using_gridappsd/index.html to run the application)
    


## Creating the sample-app application container

1.  From the command line execute the following commands to build the sample-app container

    ```console
    osboxes@osboxes> cd WSU-Restoration
    osboxes@osboxes> docker build --network=host -t wsu-restoration .
    ```

1.  Add the following to the gridappsd-docker/docker-compose.yml file

    ```` yaml
    sampleapp:
      image: wsu-restoration
      depends_on: 
        gridappsd    
    ````

1.  Run the docker application 

    ```` console
    osboxes@osboxes> cd gridappsd-docker
    osboxes@osboxes> ./run.sh
    
    # you will now be inside the container, the following starts gridappsd
    
    gridappsd@f4ede7dacb7d:/gridappsd$ ./run-gridappsd.sh
    
    ````

Next to start the application through the viz follow the directions here: https://gridappsd.readthedocs.io/en/latest/using_gridappsd/index.html#start-gridapps-d-platform
