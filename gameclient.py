from twisted.internet.protocol import ServerFactory, ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor

class GameClient(Protocol):
	def __init__(self, name, game_client_controller):
		self.name = name
		self.game_client_controller = game_client_controller
		pass

	def connectionMade(self):
		print "connect to game host!"
		self.transport.write("new " + self.name)

	def dataReceived(self, data):
		self.game_client_controller.update(data)
		self.game_client_controller.print_state()

	def connectionLost(self, reason):
		print "connection lost with host!"


class GameClientFactory(ClientFactory):
	def __init__(self, game_client_controller):
		self.name = game_client_controller.name
		self.game_client_controller = game_client_controller
		pass

	def buildProtocol(self, addr):
		return GameClient(self.name, self.game_client_controller)

class GameClientController(object):
	def __init__(self, name):
		self.name = name
		self.client_factory= GameClientFactory(self)
		self.players = []
		self.scores = {}
		pass

	def print_state(self):
		print self.scores

	def update(self, msg):
		data = msg.split()
		if data[0] == 'new':
			name = data[1]
			if name not in self.players:
				self.players.append(name)
				self.scores[name] = 5
		elif data[0] == 'score':
			name = data[1]
			action = data[2]
			num = int(data[3])
			if action == '+':
				self.scores[name] += num
			elif action == '-':
				self.scores[name] -= num
		elif data[0] == 'init':
			# initialization
			data = filter(lambda x: x != 'init', data)
			i = 0
			while (i < len(data)):
				name = data[i]
				score = int(data[i+1])
				self.players.append(name)
				self.scores[name] = score
				i += 2


if __name__ == "__main__":
	GSERVER_HOST = "localhost"
	GSERVER_PORT = 40095

	name = "xwang29"
	gcc = GameClientController(name)

	reactor.connectTCP(GSERVER_HOST, GSERVER_PORT, gcc.client_factory)
	reactor.run()
