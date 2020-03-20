# WSU-Restoration Application

This repository contains the restoration application for IEEE 9500-node model (https://github.com/GRIDAPPSD/Powergrid-Models/tree/develop/blazegraph/test/dss/WSU). The application is hosted on GridAPPS-D platform. 

## Layout

Please clone the repository https://github.com/GRIDAPPSD/gridappsd-docker (refered to as gridappsd-docker repository) next to this repository (they should both have the same parent folder)

## Creating the restoration application container

1.  From the command line execute the following commands to build the wsu-restoration container

    ```console
    osboxes@osboxes> cd WSU-Restoration
    osboxes@osboxes> docker build --network=host -t wsu-restoration-app .
    ```

1.  Add the following to the gridappsd-docker/docker-compose.yml file

    ```` yaml
    wsu_res_app:
    image: wsu-restoration-app
    volumes:
      - /opt/ibm/ILOG/CPLEX_Studio129/:/opt/ibm/ILOG/CPLEX_Studio129
    environment:
      GRIDAPPSD_URI: tcp://gridappsd:61613
    depends_on:
      - gridappsd   
      
    # Adjust the CPLEX path based on the version you have
    ````
    

1.  Run the docker application 

    ```` console
    osboxes@osboxes> cd gridappsd-docker
    osboxes@osboxes> ./run.sh
    
    # you will now be inside the container, the following starts gridappsd
    
    gridappsd@f4ede7dacb7d:/gridappsd$ ./run-gridappsd.sh
    
    ```` 

1.  Run the application container

    ```` console
    osboxes@osboxes> cd WSU-Restoration
    osboxes@osboxes> docker exec -it gridappsddocker_wsu_res_app_1 bash
    
    # Once you are inside the container, the following installs CPLEX to be used by the application 
    
    root@1b762c641f24:/usr/src/gridappsd-restoration# cd /opt/ibm/ILOG/CPLEX_Studio129/cplex/python/3.6/x86-64_linux/ ; python setup.py install
    
    # Note that the python version supported by CPLEX_Studio129 is 3.6. If you have a different version of CPLEX, it might require different version of python for interface. In such a case, make sure the application container has correct version of python installed.
    
    # Next, start the application terminal again to run the application from terminal
    
    root@1b762c641f24:/opt/ibm/ILOG/CPLEX_Studio129/cplex/python/3.6/x86-64_linux# cd /usr/src/gridappsd-restoration
    
    # The following runs the application from terminal
    
    root@1b762c641f24:/usr/src/gridappsd-restoration# cd Restoration
    root@1b762c641f24:/usr/src/gridappsd-restoration/Restoration# python main.py [simulation_ID] '{"power_system_config":  {"Line_name":"_AAE94E4A-2465-6F5E-37B1-3E72183A4E44"}}'    
    ````
    
1.  Start the platform

    ```` console
    # At this point, we are ready to start the platform using browser: localhost:8080/ 
    
    # Run the platform and take the [simulation_ID] from the browser to Step 4 for running the application in the terminal.
    
     ````
     
     
To start the application through the viz follow the directions here: https://gridappsd.readthedocs.io/en/latest/using_gridappsd/index.html#start-gridapps-d-platform

   




# Forming optimization problem

In the optimization problem, test feeders are modeled as graph; G (V, E), where V is set of nodes and E is set of edges. The graph and line parameters of the test feeder can be extracted from (https://github.com/shpoudel/D-Net). 


## Get real-time topology and load data of the test case

First, the real time topology of the test case is extracted from the operating feeder in platform (top_identify.py). Then, load data for each node is obtained (get_Load.py) and stored in json format to be used in linear power flow while writing constraints for optimization problem.

## Isolation and Restoration

Once fault is identified in the test case, Isolation.py is invoked which isolates the fault from all possible directions. Then restoration_WSU.py solves the optimization. The output of optimization is the list of switches to toggle for reconfiguration such that load restored is maximixed. Grid-forming DERs can also be utilized to form islands if required. 
