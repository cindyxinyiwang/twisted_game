from twisted.internet.protocol import ServerFactory, ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor

class GameServer(Protocol):
	def __init__(self, hostcontroller):
		self.host_controller = hostcontroller
		self.connections = {}
		pass

	def connectionMade(self):
		print "new player!"
		# initialize new client
		for k in self.host_controller.scores:
			s = self.host_controller.scores[k]
			self.transport.write("init " + k + " " + str(s) + " ")

	def dataReceived(self, data):
		msg = data
		data = data.split()
		if data[0] == 'new':
			self.connections[data[1]] = 5
			name = data[1]
			if name not in self.host_controller.players:
				self.host_controller.players.append(name)
				self.host_controller.scores[name] = 5

		elif data[0] == 'score':
			name = data[1]
			action = data[2]
			num = int(data[3])
			if action == '+':
				self.host_controller.scores[name] += num
			elif action == '-':
				self.host_controller.scores[name] -= num
		print self.host_controller.players
		# broadcaste to all clients
		self.host_controller.update(msg)

	def connectionLost(self, reason):
		print "a player lost!"


class GameServerFactory(ServerFactory):
	def __init__(self, hostcontroller):
		self.host_controller = hostcontroller
		pass

	def buildProtocol(self, addr):
		g = GameServer(self.host_controller)
		self.host_controller.serv_conns.append(g)
		return g

class GameHostController(object):
	def __init__(self):
		self.serv_factory = GameServerFactory(self)
		self.players = []
		self.scores = {}
		self.serv_conns = []

	def update(self, msg):
		for s in self.serv_conns:
			s.transport.write(msg)

if __name__ == "__main__":
	GSERVER_PORT = 40095

	game_host = GameHostController()

	reactor.listenTCP(GSERVER_PORT, game_host.serv_factory)
	reactor.run()
