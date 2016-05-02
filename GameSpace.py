import sys,pygame,math,random
from objects import *

from twisted.internet.protocol import ServerFactory, ClientFactory
from twisted.internet.protocol import Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.task import LoopingCall


class GameSpace:
  def __init__(self):
    pygame.init()

    self.size = self.width,self.height=1200,750
    self.black = 0,0,0
    self.screen = pygame.display.set_mode(self.size)
    caption=pygame.display.set_caption("Defend Your Planet!!!")
    self.coinList=[]
    self.coinMode_len=500
    self.choiceMode_len=100
    self.battleTickStart=0
    self.startTick=0
    self.mode=0
    self.winner=""

    self.itext=Text("Remaining Time: 60",30,self)
    self.itext.set_center(self.width/2,50)
    self.tick=0
    
    self.joined = False

    self.serv_conn = None
    # set up game objects
    self.set_up_objects()

  ## check what the event is and respond to the event accordingly
  def check_event(self,event):
    # any other key event input
    if event.type == pygame.QUIT:
          if self.serv_conn:
            self.serv_conn.transport.loseConnection()
          reactor.stop()
          #sys.exit()       
    elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:
              if self.serv_conn:
                self.serv_conn.transport.loseConnection()
                #sys.exit()
              reactor.stop()
    # get key current state
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RETURN]:
          self.mode=1
          self.serv_conn.transport.write(str.encode("start \r\n"))
    if keys[pygame.K_m]!=0 and self.mode==3: 
          self.player1.car.tofire=True 
          self.serv_conn.transport.write(str.encode("fire_start \r\n"))
    if keys[pygame.K_RIGHT]!=0:
          self.player1.car.setVector(15,0)
          self.serv_conn.transport.write(str.encode("right \r\n"))
    if keys[pygame.K_LEFT]!=0:
          self.player1.car.setVector(-15,0)
          self.serv_conn.transport.write(str.encode("left \r\n"))
    if keys[pygame.K_UP]!=0:
          self.player1.car.setVector(0,-15)
          self.serv_conn.transport.write(str.encode("up \r\n"))
    if keys[pygame.K_DOWN]!=0: 
          self.player1.car.setVector(0,15)
          self.serv_conn.transport.write(str.encode("down \r\n"))
    if keys[pygame.K_m]==0 and self.player1.car.tofire: 
          self.player1.car.tofire= False
          self.serv_conn.transport.write(str.encode("fire_stop \r\n"))
    ''' need to be modifed here when combined with twisted'''      
    ## keyboard events for player 2
    if keys[pygame.K_q]!=0 and self.mode==3: 
          self.player2.car.tofire=True
    if keys[pygame.K_d]!=0:
          self.player2.car.setVector(15,0)
    if keys[pygame.K_a]!=0:
          self.player2.car.setVector(-15,0)
    if keys[pygame.K_w]!=0:
          self.player2.car.setVector(0,-15)
    if keys[pygame.K_s]!=0: 
          self.player2.car.setVector(0,15)
    if keys[pygame.K_q]==0: 
          self.player2.car.tofire= False
    # in mode 2, buy facilities
    ''' need to be modifed here when combined with twisted'''
    if keys[pygame.K_1]!=0 and self.mode==2: 
          self.player2.buy_property("hospital")
    if keys[pygame.K_2]!=0 and self.mode==2: 
          self.player2.buy_property("gasStation")
    if keys[pygame.K_8]!=0 and self.mode==2: 
          self.player1.buy_property("hospital")
    if keys[pygame.K_9]!=0 and self.mode ==2: 
          self.player1.buy_property("gasStation")

  # check whether a collision has occurred. and respond to the collision accordingly
  # called by tick_objects_in_player
  def collision_handler(self,player,ilist,obj2):
    for obj1 in list(ilist):
      obj1.tick()
      col = pygame.sprite.collide_rect(obj1, obj2)
      if col == True:
        ilist.remove(obj1)
        if obj1.returnType() == 'Coin':
          player.coins+=1
        elif obj1.returnType() == 'Laser':
          obj2.points_reduction(player.laserPower)
      elif obj1.offscreen()==True:
        ilist.remove(obj1)  
      
  ## tick all objects in a given player
  ## called by tick_all_objects()
  def tick_objects_in_player(self,player):
    player.earth.tick() 
    player.car.tick()
    
    if (self.tick-self.startTick)>=self.coinMode_len: # when tick is greater than 2000, battle starts
      if self.mode <=2: self.mode=2
      self.battleTickStart=self.tick+self.choiceMode_len
      self.coinList[:]=[]
      if player.explo:
        if player.explo.exploDone==False:
          player.explo.tick()
      
      self.collision_handler(player,player.laserList, self.get_opponent(player).earth)
      self.collision_handler(player,player.laserList,self.get_opponent(player).car)
    else: # before battle starts, coin collection mode
      
      self.collision_handler(player,self.coinList,player.car)
    
    for item in player.properties:
      item.tick()     
          
  ## for every object on the screen, call its tick() 
  def tick_all_objects(self):
      self.tick_objects_in_player(self.player1)
      self.tick_objects_in_player(self.player2)
      
      delta_tick=self.tick -self.startTick
      if self.coinMode_len-delta_tick>=0: 
        self.itext.update_text("Remaining Time: "+str((self.coinMode_len-delta_tick)/10))
      else:
        self.itext.update_text("Battle Started")
      
  ## display all objects for a given player on the screen. 
  ## called by display_all_objects
  def display_player(self,iplayer):
    if iplayer.explo:
      if iplayer.explo.exploDone==False:
        self.screen.blit(iplayer.explo.rotated_image,iplayer.explo.rect) 
    if not iplayer.explo:
      self.screen.blit(iplayer.earth.orig_image,iplayer.earth.rect)
      # add all lasers to the screen
      for ilaser in iplayer.laserList:
        self.screen.blit(ilaser.rotated_image,ilaser.rect)
      # add all properties to the screen
      self.display_facilities(iplayer)
      self.screen.blit(iplayer.car.rotated_image,iplayer.car.rect)
      self.screen.blit(iplayer.car.live.image,iplayer.car.live.rect)
      self.screen.blit(iplayer.earth.live.image,iplayer.earth.live.rect)
    #for ii in iplayer.earth.fragArr:
     # ii.update(2)
      #self.screen.blit(ii.image,ii.rect)
     
  ## display all objects on the screen        
  def display_all_objects(self):
     self.screen.fill(self.black)
     self.display_player(self.player1)
     self.display_player(self.player2)
     
     self.screen.blit(self.itext.myText, (self.width/2, 20))
     if (self.tick-self.startTick)<=self.coinMode_len:
       self.display_coins()
      
  # randomly generate and display coins on the screen when tick is smaller than XX (the first one minute of the game)
  def display_coins(self):
    for icoin in self.coinList:
      self.screen.blit(icoin.rotated_image,icoin.rect)
    
  # set up game objects
  def set_up_objects(self):
    self.clock=pygame.time.Clock()
    self.player1 = Player("judy","red",self)
    self.player2 = Player("Jim","green",self)
    self.generate_coins()
    self.player1.buy_property("bank")
    self.player2.buy_property("bank")
    
  #generate coins   
  def generate_coins(self):
    counter=0
    while(1):
      counter+=1
      if counter>=200:
        break
      x=random.randint(100,self.width)
      y=random.randint(100,self.height)
      newcoin = Coin(x,y,self)
      self.coinList.append(newcoin)

  # return your opponent
  def get_opponent(self,player):
    if player.color=="red":
      return self.player2
    elif player.color=="green":
      return self.player1
      
  # display game menu before the game starts
  def display_menu(self):
    self.screen.fill(self.black)
    des1="Silly Game"
    self.txt1=Text(des1,50,self)
    des2="Game Description:"
    self.txt2=Text(des2,40,self)
    des3="First, users have 60 seconds to collect coins."
    self.txt3=Text(des3,20,self)
    des4="Then, they have 20 seconds to build their communities (e.g.,hospital, gas station)"
    self.txt4=Text(des4,20,self)
    des5=" Last, they will battle against each other and try to destroy the other's planet"
    self.txt5=Text(des5,20,self)
    des6="In the end, the one who successfully destroy its opponent's planet will win the game"
    self.txt6=Text(des6,20,self)
    des7="Press ENTER to Start Playing"
    self.txt7=Text(des7,40,self)
    self.txt1.set_center(self.width/2, 100)
    self.txt2.set_center(self.width/2, 150)
    self.txt3.set_center(self.width/2, 250)
    self.txt4.set_center(self.width/2, 300)
    self.txt5.set_center(self.width/2, 350)
    self.txt6.set_center(self.width/2, 400)
    self.txt7.set_center(self.width/2, 500)
    self.screen.blit(self.txt1.myText, self.txt1.rect)
    self.screen.blit(self.txt2.myText, self.txt2.rect)
    self.screen.blit(self.txt3.myText, self.txt3.rect)
    self.screen.blit(self.txt4.myText, self.txt4.rect)
    self.screen.blit(self.txt5.myText, self.txt5.rect)
    self.screen.blit(self.txt6.myText, self.txt6.rect)
    self.screen.blit(self.txt7.myText, self.txt7.rect)
    
  # the state when game is over
  def gameover_state(self,winner):
    self.screen.fill(self.black)
    des1="Game Over"
    self.txt1=Text(des1,50,self)
    des2="Victory belongs to the %s car" %winner
    self.txt2=Text(des2,50,self)
    self.txt1.set_center(self.width/2, 200)
    self.txt2.set_center(self.width/2, 350)
    self.screen.blit(self.txt1.myText, self.txt1.rect)
    self.screen.blit(self.txt2.myText, self.txt2.rect)
    
  # check whether game is over  
  def check_game_over(self):
    if self.player1.earth.points<=0:
      self.winner=self.player2
      return 1
    elif self.player2.earth.points<=0:
      self.winner=self.player1
      return 1
    else:
      return 0
      
  # build your community and prepare for the battle
  def buildCommunity(self):
    self.screen.fill(self.black)
    des1="Use your money to build your community"
    self.txt1=Text(des1,30,self)
    des11="Choose the following by pressing keys"
    self.txt11=Text(des11,30,self)
    des2="1:Planet's Life ($40): + 40 per sec" 
    self.txt2=Text(des2,30,self)
    des3="2:Laser Power ($30): + 5 per beam" 
    self.txt3=Text(des3,30,self)
    self.txt1.set_center(self.width/2, 150)
    self.txt11.set_center(self.width/2, 200)
    self.txt2.set_center(self.width/2, 250)
    self.txt3.set_center(self.width/2, 350)
    self.screen.blit(self.txt1.myText, self.txt1.rect)
    self.screen.blit(self.txt11.myText, self.txt11.rect)
    self.screen.blit(self.txt2.myText, self.txt2.rect)
    self.screen.blit(self.txt3.myText, self.txt3.rect)
    # display the purchased facility icons
    self.display_facilities(self.player1)
    self.display_facilities(self.player2)
    # check whether time is up
    if self.tick > self.battleTickStart:
      self.mode=3
  # display all purchased facilities on screen 
  def display_facilities(self,iplayer):
    for item in iplayer.properties:
         self.screen.blit(item.rotated_image,item.rect)
         self.screen.blit(item.displayText,item.tmp.rect)
             
  def main(self):
    # 3: start game loop
    
    self.tick+=1
      
	  ## check and respond to the event for a given tick
    for event in pygame.event.get():
      self.check_event(event)

    if not self.joined:
      # the other user hasn't joined the game yet
      self.display_menu()
      return

    if self.mode==4: 
      ## game is over
      self.gameover_state(self.winner.color)
    elif self.mode ==2:
      ## build your community and prepare for the battle
      self.buildCommunity()
    elif self.mode == 0:
      ## before starting the game
      self.startTick=self.tick
      self.display_menu()
    else:
      # send a tick to every game object
      self.tick_all_objects()
      # check whether game is over
      #if self.check_game_over() != 0:
       # self.mode=4
      # display the game objects
      self.display_all_objects()
      
    pygame.display.flip()

class GameServer(LineReceiver):
  def __init__(self, hostcontroller, gs):
    self.host_controller = hostcontroller
    self.connections = {}
    self.gs = gs
    self.gs.serv_conn = self
    pass

  def connectionMade(self):
    self.gs.joined = True
    print ("new player!")
    # send coin config to client
    for c in self.gs.coinList:
      x, y = c.rect.center
      string = "coin " + str(x) + " " + str(y) + "\r\n"
      print (string)
      self.transport.write(str.encode(string))

    # initialize new client
    #for k in self.host_controller.scores:
    #  s = self.host_controller.scores[k]
    #  self.transport.write("init " + k + " " + str(s) + " ")

  def lineReceived(self, data):
    data = data.decode("utf-8")
    data = data.split()
    if data[0] == 'new':
      self.connections[data[1]] = 5
      name = data[1]
      if name not in self.host_controller.players:
        self.host_controller.players.append(name)
        self.host_controller.scores[name] = 5

    elif data[0] == 'right':
      self.gs.player2.car.setVector(15, 0)
    elif data[0] == 'left':
      self.gs.player2.car.setVector(-15, 0)
    elif data[0] == 'up':
      self.gs.player2.car.setVector(0, -15)
    elif data[0] == 'down':
      self.gs.player2.car.setVector(0, 15)
    elif data[0] == 'fire_start':
      self.gs.player2.car.tofire = True
    elif data[0] == 'fire_stop':
      self.gs.player2.car.tofire = False
    elif data[0] == 'score':
      name = data[1]
      action = data[2]
      num = int(data[3])
      if action == '+':
        self.host_controller.scores[name] += num
      elif action == '-':
        self.host_controller.scores[name] -= num
    print (self.host_controller.players)
    # broadcaste to all clients
    #self.host_controller.update(msg)

  def connectionLost(self, reason):
    print(reason)
    print ("a player lost!")


class GameServerFactory(ServerFactory):
  def __init__(self, hostcontroller, gs):
    self.host_controller = hostcontroller
    self.gs = gs
    pass

  def buildProtocol(self, addr):
    g = GameServer(self.host_controller, gs)
    self.host_controller.serv_conns.append(g)
    return g

class GameHostController(object):
  def __init__(self, gs):
    self.serv_factory = GameServerFactory(self, gs)
    self.players = []
    self.scores = {}
    self.serv_conns = []
    self.gamespace = gs

  def update(self, msg):
    for s in self.serv_conns:
      s.transport.write(msg)


if __name__=='__main__':

  GSERVER_PORT = 40095


  gs = GameSpace()
  #gs.main()

  lc = LoopingCall(gs.main)
  lc.start(1/60)

  game_host = GameHostController(gs)

  reactor.listenTCP(GSERVER_PORT, game_host.serv_factory)
  reactor.run()

  


