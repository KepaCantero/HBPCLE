"""
Interface for gzserver and gzbridge spawning classes.
"""

__author__ = 'Alessandro Ambrosano'


class IGazeboServerInstance(object):   # pragma: no cover
    """
    Takes care of starting a gzserver process somewhere, connect it to the given roscore.
    Each implementation has to take care of providing the methods start, stop and restart as
    well as a property containing the gzserver master URI.
    """

    def start(self, ros_master_uri):
        """
        Starts a gzserver instance connected to the local roscore (provided by
        ros_master_uri)

        :param ros_master_uri The ros master uri where to connect gzserver.
        """
        raise NotImplementedError("This method was not implemented in the concrete implementation")

    def stop(self):
        """
        Stops the gzserver instance.
        """
        raise NotImplementedError("This method was not implemented in the concrete implementation")

    @property
    def gazebo_master_uri(self):
        """
        Returns a string containing the gazebo master
        URI (like:'http://bbpviz001.cscs.ch:11345')
        """
        raise NotImplementedError("This method was not implemented in the concrete implementation")

    def restart(self, ros_master_uri):
        """
        Restarts the gzserver instance.

        :param ros_master_uri The ros master uri where to connect gzserver.
        """
        raise NotImplementedError("This method was not implemented in the concrete implementation")


class IGazeboBridgeInstance(object):
    """
    Takes care of starting a gzserver instance somewhere.
    """

    def start(self):
        """
        Starts the gzbridge instance represented by the object.
        """
        raise NotImplementedError("This method was not implemented in the concrete implementation")

    def stop(self):
        """
        Stops the gzbridge instance represented by the object.
        """
        raise NotImplementedError("This method was not implemented in the concrete implementation")

    def restart(self):
        """
        Restarts the gzbridge instance represented by the object.
        """
        raise NotImplementedError("This method was not implemented in the concrete implementation")
