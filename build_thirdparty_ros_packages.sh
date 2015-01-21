#!/bin/bash -e
# ------------------------------------------------------------------
# [peppicel] Get all the needed third party ROS packages and build 
#            a GNU module out of them.
#            This script needs to be run on an HBP virtual machine 
#            that can access the NFS4. For example a CLEserver instance
#            is a good place. Before running that script, 
#            run "chmod a+w /nfs4/bbp.epfl.ch/sw/neurorobotics/ros-thirdparty"
#	     on a machine where you are logged with your username and where
#            the nfs4 is mounted.
# 	     After the script execution, run the opposite:
#            "chmod a-w /nfs4/bbp.epfl.ch/sw/neurorobotics/ros-thirdparty"
# ------------------------------------------------------------------

# We need python 2.7
source /opt/rh/python27/enable

# Get the proper modules
export MODULEPATH=$MODULEPATH:/nfs4/bbp.epfl.ch/sw/neurorobotics/modulefiles
module load boost/1.55zlib-rhel6-x86_64-gcc4.4
module load ros/hydro-rhel6-x86_64-gcc4.4
module load gazebo/4.0-rhel6-x86_64-gcc4.8.2
module load opencv/2.4.9-rhel6-x86_64-gcc4.8.2
module load sdf/2.0-rhel6-x86_64-gcc4.4
module load tbb/4.0.5-rhel6-x86_64-gcc4.4

source $ROS_SETUP_FILE

# Create a python venv in order to get the bases ROS install tools
virtualenv build_venv
. build_venv/bin/activate
pip install catkin_pkg
pip install empy
pip install PyYAML
pip install rospkg
pip install netifaces
pip install rosinstall
pip install rosinstall_generator

rm -rf build
mkdir -p build/src
cd build/src
# ROS bridge
git clone https://github.com/RobotWebTools/rosbridge_suite.git
# ROS auth (dependency of ROS bridge)
git clone -b develop https://github.com/WPI-RAIL/rosauth.git

cd ..
catkin_make -DCATKIN_ENABLE_TESTING=0 -DCMAKE_INSTALL_PREFIX=/nfs4/bbp.epfl.ch/sw/neurorobotics/ros-thirdparty/hydro/rhel-6.5-x86_64/gcc-4.4.7/x86_64/ install

