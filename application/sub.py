from kazoo.client import KazooClient
from kazoo.recipe.watchers import DataWatch
from middleware.sub import *
from logger import get_logger
from kazoo.exceptions import NoNodeError, NodeExistsError

sub_direct = 1
sub_broker = 2


class Subscriber:

    def __init__(self, ip_self, ip_zookeeper, comm_type, logfile='log/sub.log', name='', zk_root=''):
        self.name = name
        self.zk_root = zk_root
        self.ip = ip_self
        self.ip_b = None
        self.comm_type = comm_type
        self.exited = False
        self.logger = get_logger(logfile)
        self.zk_client = KazooClient(hosts=ip_zookeeper)
        self.sub_mid = None

    def create_middleware(self):
        ip_b, _ = self.zk_client.get("%s/Leader" % self.zk_root)
        ip_b = ip_b.decode()
        self.ip_b = ip_b
        if self.comm_type == sub_direct:
            self.sub_mid = SubDirect(self.ip, self.ip_b, self.zk_client, zk_root=self.zk_root)
        elif self.comm_type == sub_broker:
            self.sub_mid = SubBroker(self.ip, self.ip_b)
        else:
            print("Error in communication type: Only 1 and 2 are accepted.")
            exit(1)

    def update(self, data, stat, ver):
        self.ip_b = data.decode()
        self.sub_mid.update_broker_ip(self.ip_b)

    def __get_broker_ip(self):
        self.ip_b = self.zk_client.get("%s/Leader"%self.zk_root)

    def register(self, topics):
        self.zk_client.start()
        try:
            self.zk_client.create('%s/Subscriber/%s' % (self.zk_root, self.name),
                                  ('%s,%s' % (self.ip, '')).encode(),
                                  ephemeral=True, makepath=True)
        except NodeExistsError:
            pass

        self.create_middleware()

        for t in topics:
            try:
                c = self.zk_client.get_children("%s/Topic/%s/Sub"%(self.zk_root, t['topic']))
            except NoNodeError:
                self.zk_client.create("%s/Topic/%s/Sub"%(self.zk_root, t['topic']), makepath=True, ephemeral=False)
                c = []
            id = self.zk_client.create("%s/Topic/%s/Sub/Sub"%(self.zk_root, t['topic']), sequence=True, makepath=True, ephemeral=True)
            history = t["history"]
            s_h = ','.join([self.ip, str(history)])
            self.zk_client.set(id, s_h.encode())

            self.logger.info('sub register to broker on %s. ip=%s, topic=%s' % (self.ip_b, self.ip, t['topic']))

        self.sub_mid.register(topics)
        DataWatch(self.zk_client, "%s/Leader"%self.zk_root, self.update)
        return 0

    def receive(self):
        msg = None
        if self.comm_type == sub_direct:
            self.sub_mid.start_receive_threads()
            msg = self.sub_mid.receive()
        if self.comm_type == sub_broker:
            msg = self.sub_mid.notify()
        if msg:
            self.logger.info('receive a msg=%s' % msg)
        return msg

    '''
    subscriber cancels a topic
    '''
    def unregister(self, topic):
        self.sub_mid.unregister(topic)

    '''
    subscriber wants to exit the system
    '''
    def exit(self):
        self.exited = True
        self.zk_client.stop()
        self.zk_client.close()
        self.sub_mid.exit()
        return 0


