# Use the base application container to allow the application to be controlled
# from the gridappsd container.
FROM gridappsd/app-container-base:develop

# Add the TIMESTAMP variable to capture the build information from 
# the travis docker build command and add them to the image.
ARG TIMESTAMP
RUN echo $TIMESTAMP > /dockerbuildversion.txt 
# RUN apt-get update \
#     && apt-get install -y \
#        libatlas3-base

# Pick a spot to put our application code
# (note gridappsd-python is located at /usr/src/gridappsd-python)
# and is already installed in the app-container-base environment.
WORKDIR /usr/src/gridappsd-restoration

# Add dependencies to the requirements.txt file before
# uncommenting the next two lines
# COPY requirements.txt ./
# RUN RUN pip install --no-cache-dir -r requirements.txt
# RUN apt-get install software-properties-common
# RUN add-apt-repository ppa:openjdk-r/ppa
# RUN apt-get update
# RUN apt-get install -y openjdk-8-jdk
RUN pip install networkx numpy pulp

# Copy all of the source over to the container.
COPY . .

# RUN chmod +x cplex_studio129.linux-x86-64.bin
# RUN ./cplex_studio129.linux-x86-64.bin
# Use a symbolic link to the sample app rather than having to
# mount it at run time (note can still be overriden in docker-compose file)
RUN ln -s /usr/src/gridappsd-restoration/wsu_res_app.config /appconfig
# CMD cd /opt/ibm/ILOG/CPLEX_Studio129/cplex/python/3.6/x86-64_linux/ ; python setup.py install



