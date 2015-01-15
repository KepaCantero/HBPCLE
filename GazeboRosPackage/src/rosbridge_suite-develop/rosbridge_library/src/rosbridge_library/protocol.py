# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

#pylint: skip-file

import rospy
import time

from rosbridge_library.internal.exceptions import InvalidArgumentException
from rosbridge_library.internal.exceptions import MissingArgumentException

# from rosbridge_library.internal.pngcompression import encode
from rosbridge_library.capabilities.fragmentation import Fragmentation
from rosbridge_library.util import json


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class Protocol:

    """ The interface for a single client to interact with ROS.

    See rosbridge_protocol for the default protocol used by rosbridge

    The lifecycle for a Protocol instance is as follows:
    - Pass incoming messages from the client to incoming
    - Propagate outgoing messages to the client by overriding outgoing
    - Call finish to clean up resources when the client is finished

    """

    # fragment_size can be set per client (each client has its own instance of protocol)
    # ..same for other parameters
    fragment_size = None
    png = None
    # buffer used to gather partial JSON-objects (could be caused by small
    # tcp-buffers or similar..)
    buffer = ""
    old_buffer = ""
    busy = False
    # if this is too low, ("simple")clients network stacks will get flooded
    # (when sending fragments of a huge message..)
    # .. depends on message_size/bandwidth/performance/client_limits/...
    # !! this might be related to (or even be avoided by using) throttle_rate !!
    delay_between_messages = 0.01
    # global list of non-ros advertised services
    external_service_list = {}

    parameters = None

    def __init__(self, client_id):
        """ Keyword arguments:
        client_id -- a unique ID for this client to take.  Uniqueness is
        important otherwise there will be conflicts between multiple clients
        with shared resources

        """
        self.client_id = client_id
        self.capabilities = []
        self.operations = {}

        if self.parameters:
            self.fragment_size = self.parameters["max_message_size"]
            self.delay_between_messages = self.parameters[
                "delay_between_messages"]

    # added default message_string=""
    # to allow recalling incoming until buffer is empty without giving a parameter
    # --> allows to get rid of (..or minimize) delay between client-side sends
    def incoming(self, message_string=""):
        """ Process an incoming message from the client

        Keyword arguments:
        message_string -- the wire-level message sent by the client

        """
        self.buffer = self.buffer + message_string
        msg = None

        # take care of having multiple JSON-objects in receiving buffer
        # ..first, try to load the whole buffer as a JSON-object
        try:
            msg = self.deserialize(self.buffer)
            self.buffer = ""

        # if loading whole object fails try to load part of it
        # (from first opening bracket "{" to next closing bracket "}"
        # .. this causes Exceptions on "inner" closing brackets -->
        # so I suppressed logging of deserialization errors
        except Exception as e:

            opening_brackets = [
                i for i, letter in enumerate(self.buffer) if letter == '{']
            closing_brackets = [
                i for i, letter in enumerate(self.buffer) if letter == '}']

            for start in opening_brackets:
                for end in closing_brackets:
                    try:
                        msg = self.deserialize(self.buffer[start:end + 1])
                        if msg.get("op", None) is not None:
                            # TODO: check if throwing away leading data like
                            # this is okay.. loops look okay..
                            self.buffer = self.buffer[end + 1:len(self.buffer)]
                            # jump out of inner loop if json-decode succeeded
                            break
                    except Exception as e:
                        # debug json-decode errors with this line
                        # print e
                        pass
                # if load was successfull --> break outer loop, too.. -> no
                # need to check if json begins at a "later" opening bracket..
                if msg is not None:
                    break

        # if decoding of buffer failed .. simply return
        if msg is None:
            return

        # process fields JSON-message object that "control" rosbridge
        mid = None
        if "id" in msg:
            mid = msg["id"]
        if "op" not in msg:
            if "receiver" in msg:
                self.log("error", "Received a rosbridge v1.0 message.  \
                         Please refer to rosbridge.org for the correct \
                         format of rosbridge v2.0 messages.  \
                         Original message was: %s" %
                         message_string)
            else:
                self.log("error", "Received a message without an op.  \
                         All messages require 'op' field with value one of: %s.  \
                         Original message was: %s" %
                         (self.operations.keys(), message_string), mid)
            return
        op = msg["op"]
        if op not in self.operations:
            self.log("error", "Unknown operation: %s.  Allowed operations: %s" %
                     (op, self.operations.keys()), mid)
            return
        if "fragment_size" in msg.keys():
            self.fragment_size = msg["fragment_size"]
            # print "fragment size set to:", self.fragment_size
        if "message_intervall" in msg.keys() and is_number(msg["message_intervall"]):
            self.delay_between_messages = msg["message_intervall"]
        if "png" in msg.keys():
            self.png = msg["msg"]

        # now try to pass message to according operation
        try:
            self.operations[op](msg)
        except Exception as exc:
            self.log("error", "%s: %s" % (op, str(exc)), mid)

        # if anything left in buffer .. re-call self.incoming
        # TODO: check what happens if we have "garbage" on tcp-stack -->
        # infinite loop might be triggered! .. might get out of it when next
        # valid JSON arrives since only data after last 'valid' closing bracket
        # is kept
        if len(self.buffer) > 0:
            # try to avoid infinite loop..
            if self.old_buffer != self.buffer:
                self.old_buffer = self.buffer
                self.incoming()

    def outgoing(self, message):
        """ Pass an outgoing message to the client.  This method should be
        overridden.

        Keyword arguments:
        message -- the wire-level message to send to the client

        """
        pass

    def send(self, message, cid=None):
        """ Called internally in preparation for sending messages to the client

        This method pre-processes the message then passes it to the overridden
        outgoing method.

        Keyword arguments:
        message -- a dict of message values to be marshalled and sent
        cid     -- (optional) an associated id

        """
        serialized = self.serialize(message, cid)
        if serialized is not None:
            if self.png == "png":
                # TODO: png compression on outgoing messages
                # encode message
                pass

            fragment_list = None
            if self.fragment_size is not None and len(serialized) > self.fragment_size:
                mid = message.get("id", None)

                fragment_list = Fragmentation(self).fragment(
                    message, self.fragment_size, mid)

            # fragment list not empty -> send fragments
            if fragment_list is not None:
                for fragment in fragment_list:
                    self.outgoing(json.dumps(fragment))
                    time.sleep(self.delay_between_messages)
            # else send message as it is
            else:
                self.outgoing(serialized)
                time.sleep(self.delay_between_messages)

    def finish(self):
        """ Indicate that the client is finished and clean up resources.

        All clients should call this method after disconnecting.

        """
        for capability in self.capabilities:
            capability.finish()

    def serialize(self, msg, cid=None):
        """ Turns a dictionary of values into the appropriate wire-level
        representation.

        Default behaviour uses JSON.  Override to use a different container.

        Keyword arguments:
        msg -- the dictionary of values to serialize
        cid -- (optional) an ID associated with this.  Will be logged on err.

        Returns a JSON string representing the dictionary
        """
        try:
            return json.dumps(msg)
        except:
            if cid is not None:
                # Only bother sending the log message if there's an id
                self.log("error", "Unable to serialize %s message to client"
                         % msg["op"], cid)
            return None

    def deserialize(self, msg, cid=None):
        """ Turns the wire-level representation into a dictionary of values

        Default behaviour assumes JSON. Override to use a different container.

        Keyword arguments:
        msg -- the wire-level message to deserialize
        cid -- (optional) an ID associated with this.  Is logged on error

        Returns a dictionary of values

        """
        try:
            return json.loads(msg)
        except Exception as e:
            raise
            # return None

    def register_operation(self, opcode, handler):
        """ Register a handler for an opcode

        Keyword arguments:
        opcode  -- the opcode to register this handler for
        handler -- a callback function to call for messages with this opcode

        """
        self.operations[opcode] = handler

    def unregister_operation(self, opcode):
        """ Unregister a handler for an opcode

        Keyword arguments:
        opcode -- the opcode to unregister the handler for

        """
        if opcode in self.operations:
            del self.operations[opcode]

    def add_capability(self, capability_class):
        """ Add a capability to the protocol.

        This method is for convenience; assumes the default capability
        constructor

        Keyword arguments:
        capability_class -- the class of the capability to add

        """
        self.capabilities.append(capability_class(self))

    def log(self, level, message, lid=None):
        """ Log a message to the client.  By default just sends to stdout

        Keyword arguments:
        level   -- the logger level of this message
        message -- the string message to send to the user
        lid     -- an associated for this log message

        """
        stdout_formatted_msg = None
        if lid is not None:
            stdout_formatted_msg = "[Client %s] [id: %s] %s" % (
                self.client_id, lid, message)
        else:
            stdout_formatted_msg = "[Client %s] %s" % (self.client_id, message)

        if level == "error" or level == "err":
            rospy.logerr(stdout_formatted_msg)
        elif level == "warning" or level == "warn":
            rospy.logwarn(stdout_formatted_msg)
        elif level == "info" or level == "information":
            rospy.loginfo(stdout_formatted_msg)
        else:
            rospy.logdebug(stdout_formatted_msg)