import zmq
import json


class PublisherDirectly:
    def __init__(self, ip_address, broker_address, strength=None):
        self.ip_address = ip_address
        self.strength = strength
        self.socket = None
        self.broker_address = broker_address
        self.socket_broker = None
        self.context = zmq.Context()

    def publish(self, topic, value):
        if self.socket == None:
            self.__socket_bind()
            # print ("haven't registered a publisher")
        else:
            #self.socket.send_json({"topic": topic, "value": value})
            self.socket.send_json({"type": "publish_req", "topic": topic,
                                                       "value": value, 'ip': self.ip_address})
        return 0

    def register(self, topic):
        self.__socket_bind()
        self.__reg_broker(topic)
        return 0

    def __socket_bind(self):
        if self.socket is None:
            self.socket = self.context.socket(zmq.PUB)
            self.socket.bind("tcp://*:%s" % self.ip_address.split(":")[2])

    def __reg_broker(self, topic):
        context = zmq.Context()
        self.socket_broker = context.socket(zmq.REQ)
        self.socket_broker.connect(self.broker_address)
        self.socket_broker.send_json(
                        (json.dumps({'type': 'add_publisher', 'ip': self.ip_address, 'topic': topic})))
        #if isinstance(topic, list):
        #    for t in topic:
        #        self.socket_broker.send_json(
        #            (json.dumps({'type': 'add_publisher', 'ip': self.ip_address, 'topic': t})))
        #        msg = self.socket_broker.recv_json()
        #else:
        #    self.socket_broker.send_json((json.dumps({'type': 'add_publisher',
         #                                             'ip': self.ip_address, 'topic': topic})))
            #msg = self.socket_broker.recv_json()
        msg = self.socket_broker.recv_json()
        context2 = zmq.Context()

    '''
    if a leader broker dies, watcher should use this function to update connection with the new leader broker
    '''
    def update_broker_bind(self, new_broker_address):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(new_broker_address)
        self.socket_broker.close()
        self.socket_broker = socket
        self.broker_address = new_broker_address

    '''
    publisher wants to cancel a topic
    '''
    def unregister(self, topic):
        self.socket_broker.send_json((json.dumps({'type': 'pub_unregister_topic', 'ip': self.ip_address, 'topic': topic})))
        return 0

    '''
    publisher wants to exit the system
    '''
    def drop_system(self):
        # self.socket_broker.send_json((json.dumps({'type': 'pub_exit_system', 'ip': self.ip_address})))
        return 0


class PublisherViaBroker:
    def __init__(self, ip_address, broker_address, strength=None):
        self.ip_address = ip_address
        self.strength = strength
        self.socket = None
        self.broker_address = broker_address
        self.socket_broker = None
        self.context = zmq.Context()

    def publish(self, topic, value):
        if self.socket == None:
            self.__socket_bind()
            # print ("haven't registered a publisher")
        else:
            # self.__socket_bind()
            # self.socket.send_string(json.dumps({"type": "publish_req", "topic": topic, "value": value}))
            self.socket_broker.send_string(json.dumps({"type": "publish_req", "topic": topic,
                                                       "value": value, 'ip': self.ip_address}))
            msg = self.socket_broker.recv_json()
        return 0

    def register(self, topic):
        self.__socket_bind()
        self.__reg_broker(topic)
        return 0

    def __socket_bind(self):
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % self.ip_address.split(":")[2])
        # self.socket.bind(self.ip_address)

    def __reg_broker(self, topic):
        context = zmq.Context()
        self.socket_broker = context.socket(zmq.REQ)
        self.socket_broker.connect(self.broker_address)
        self.socket_broker.send_json(
            (json.dumps({'type': 'add_publisher', 'ip': self.ip_address, 'topic': topic})))
        '''
        if isinstance(topic, list):
            for t in topic:
                self.socket_broker.send_json(
                    (json.dumps({'type': 'add_publisher', 'ip': self.ip_address, 'topic': t})))
                msg = self.socket_broker.recv_json()
        else:
            self.socket_broker.send_json((json.dumps({'type': 'add_publisher',
                                                      'ip': self.ip_address, 'topic': topic})))
            msg = self.socket_broker.recv_json()
        '''
        msg = self.socket_broker.recv_json()
        context2 = zmq.Context()

    '''
    publisher wants to cancel a topic
    '''
    def unregister(self, topic):
        self.socket_broker.send_json((json.dumps({'type': 'pub_unregister_topic', 'ip': self.ip_address, 'topic': topic})))
        return 0

    '''
    publisher wants to exit the system
    '''
    def drop_system(self):
        # self.socket_broker.send_json((json.dumps({'type': 'pub_exit_system', 'ip': self.ip_address})))
        return 0

    '''
    if a leader broker dies, watcher should use this function to update connection with the new leader broker
    '''
    def update_broker_bind(self, new_broker_address):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(new_broker_address)
        self.socket_broker.close()
        self.socket_broker = socket
        self.broker_address = new_broker_address
