import sys,pygame,math,random


class Player():
  def __init__(self,player_name,car_color,gs):
    self.name=player_name
    self.gs=gs
    self.color=car_color
    self.properties=[]
    self.earth=Earth(gs)
    self.explo=None
    self.car=Car(car_color,self,gs)
    self.laserList=[]
    self.coins=0
    self.laserPower=5
    if car_color=='red':
      self.earth.rect.center=(50,400)
    elif car_color=='green':
      self.earth.rect.center=(gs.width-50,400)
    
  def buy_property(self,type):
    prop=None
    if type == "hospital":
      if self.point_deduction(40):
        prop = hospital(self,self.gs)
    elif type == "bank":
      prop = bank(self,self.gs)
    elif type == "gasStation":
      if self.point_deduction(30):
        prop = gasStation(self,self.gs)
    if prop != None:
      x,y=self.calculate_new_facility_position()  
      prop.set_position(x,y)
      if self.color=='green':
        x-=100
      else:
        x+=100
      prop.display_points(x,y) 
      self.properties.append(prop)

  # after purchasing a facility, point deduction
  def point_deduction(self,points):
    if self.coins-points>=0:
      self.coins-=points
    else:
      print ('zero balance')
 
  # automatically calculate the new facility position on screen
  def calculate_new_facility_position(self):
    y=len(self.properties)*90+50
    if self.color=='red':
      x=40
    elif self.color =='green':
      x=self.gs.width-40
    return x,y

class Property(pygame.sprite.Sprite):
  def __init__(self,type,fileName,gs=None):
    pygame.sprite.Sprite.__init__(self)
    self.type = type
    self.gs = gs
    self.image=pygame.image.load(fileName)
    self.size = self.image.get_size()
    #self.image = pygame.transform.scale(self.image, (int(self.size[0]*0.25), int(self.size[1]*0.25)))
    self.image=pygame.transform.smoothscale(self.image, (80,70))
    self.rect = self.image.get_rect()
    
    self.rotated_image=self.image
    self.orig_image = self.image
    self.px=self.rect.centerx
    self.py=self.rect.centery
    self.text="0"
    
    
  def set_position(self,x,y):
    self.rect.center=(x,y)
    
  def display_points(self,x,y):
    self.textX=x
    self.textY=y
    self.tmp=Text(self.text,20,self.gs)
    self.displayText=self.tmp.myText
    self.tmp.set_center(x,y)


# life points of earth  
class red_cross(Property):
  def __init__(self,player,gs=None):
    Property.__init__(self,"bank","media/red-cross.png",gs) 
    self.player=player
    self.text="Total life : "+str(player.coins*10)
  
  def tick(self):
    self.text="Total $: "+str(self.player.coins*10)
    self.display_points(self.textX,self.textY)      

class hospital(Property):
  def __init__(self,player,gs=None):
    Property.__init__(self,"hospital","media/hospital.png",gs)
    self.text="Planet's Life: +40/sec"
  # add life points to the earth 
  def tick(self):
    player.earth.points+=40
    
        
class bank(Property):
  def __init__(self,player,gs=None):
    Property.__init__(self,"bank","media/bank.png",gs) 
    self.player=player
    self.text="Total $: "+str(player.coins*10)
  
  def tick(self):
    self.text="Total $: "+str(self.player.coins*10)
    self.display_points(self.textX,self.textY)

class gasStation(Property):
  def __init__(self,player,gs=None):
    Property.__init__(self,"gas-station","media/gas-station.png",gs) 
    # increase laser power of the car
    player.laserPower+=4
    self.text="Laser Power: "+str(player.laserPower)+"/beam"

  def tick(self):
    self.display_points(self.textX,self.textY)
 
 
# after car's death, create fragments    
class Fragment(pygame.sprite.Sprite): 
  def __init__(self, pos):
    pygame.sprite.Sprite.__init__(self)
    self.pos = [0.0,0.0]
    self.pos[0] = pos[0]
    self.pos[1] = pos[1]
    self.image = pygame.Surface((10,10))
    self.image.set_colorkey((178,34,34)) 
    pygame.draw.circle(self.image, (random.randint(1,64),0,0), (5,5), 
                                        random.randint(2,5))
    self.image = self.image.convert_alpha()
    self.rect = self.image.get_rect()
    self.rect.center = self.pos #if you forget this line the sprite sit in the topleft corner
    self.lifetime = 1 + random.random()*5 # max 6 seconds
    self.time = 0.0
    self.fragmentmaxspeed = 200 * 2 # try out other factors !
    self.dx = random.randint(-self.fragmentmaxspeed,self.fragmentmaxspeed)
    self.dy = random.randint(-self.fragmentmaxspeed,self.fragmentmaxspeed)
            
  def update(self, seconds):
      self.time += seconds
      if self.time > self.lifetime:
          self.kill() 
      self.pos[0] += self.dx * seconds
      self.pos[1] += self.dy * seconds
      
      self.dy += 9.81 # gravity suck fragments down
      self.rect.centerx = round(self.pos[0],0)
      self.rect.centery = round(self.pos[1],0)
    
      
''' text object that will be displayed on the screen  '''     
class Text():
  def __init__(self,text,fontsize,gs=None):
    #Text through GUI
    self.myFont = pygame.font.SysFont("comicsansms", fontsize)    
    self.myText = self.myFont.render(text, 1,(0, 128, 0))
    self.rect = self.myText.get_rect()
   
  def update_text(self,newText):
    self.myText = self.myFont.render(newText, 1, (0, 128, 0))
    
  def set_center(self,x,y):
    self.rect.center=(x,y)
    
    
class Car(pygame.sprite.Sprite):
  def __init__(self,icolor,player,gs=None):
    pygame.sprite.Sprite.__init__(self)
    self.color=icolor
    self.gs = gs
    self.player=player
    self.image=pygame.image.load("media/car-"+self.color+".png")
   
    self.size = self.image.get_size()
    # create a 2X smaller image than the original image
    self.image = pygame.transform.scale(self.image, (int(self.size[0]*0.4), int(self.size[1]*0.4)))
    self.rect = self.image.get_rect()
    self.rotated_image=self.image
    self.orig_image = self.image
    if self.color == 'red':
      self.rect.center=(50,200)
    elif self.color=='green':
      self.rect.center=(gs.width-50,200)
      
    # fire laser beams right now ?
    self.tofire=False
    self.setDig = False
    self.degree = 0
    self.points=500
    self.fullPoints=500
    self.dgr=0
    self.dx=0
    self.dy=0
    
    self.live=Livebar(self)

  def tick(self):
    mx,my = pygame.mouse.get_pos()
    self.live.update(0.1)
    #degr=-math.atan2(my-self.rect.centery,mx-self.rect.centerx)/math.pi*180-90
    self.move()
    self.setVector(0,0)
    # prevents movment while firing
    if self.tofire ==True:
      # emit a laser beam block
      self.fire(mx,my)
    #else:
      
      #self.rotated_image= pygame.transform.rotate(self.orig_image,self.dgr)
    if self.points <=5:
      Sprite.kill(self)
  
  def fire(self,mx,my):
    # calc angle of fire
    if self.setDig:
      px,py = self.rect.center
      ilaser=Laser(px,py, self.degree, self.gs)
      self.player.laserList.append(ilaser)
      print (self.degree)
    else:
      px,py = self.rect.center
      radius=math.atan2(my-py,mx-px)
      px+=40*math.cos(radius)
      py+=40*math.sin(radius)
      fire_angle=math.atan2(my-py,mx-px)
      self.degree = fire_angle

      ilaser=Laser(px,py,fire_angle,self.gs)
      self.player.laserList.append(ilaser)
    
  def setVector(self,x,y):
    self.dx=x
    self.dy=y
    
  def move(self):
    ## rotate car's orientation:
    if self.dx <0:
      self.rotated_image= pygame.transform.rotate(self.orig_image,90)
    elif self.dx>0:
      self.rotated_image= pygame.transform.rotate(self.orig_image,-90)
    elif self.dy<0:
      self.rotated_image= pygame.transform.rotate(self.orig_image,0) 
    elif self.dy>0:  
      self.rotated_image= pygame.transform.rotate(self.orig_image,180) 
   
    self.rect.centerx+=self.dx
    self.rect.centery+=self.dy

  ## reduce points if collision occurs
  def points_reduction(self,laserPower):
      self.points-=laserPower
      

''' coin '''      
class Coin(pygame.sprite.Sprite):
  def __init__(self,x,y,gs=None):
    pygame.sprite.Sprite.__init__(self)
    self.gs = gs
    self.image=pygame.image.load("media/coin.png")
    self.size = self.image.get_size()
    self.image = pygame.transform.scale(self.image, (int(self.size[0]*0.2), int(self.size[1]*0.2)))
    self.rect = self.image.get_rect()
    self.rect.center=(x,y)
    self.rotated_image=self.image
    self.orig_image = self.image
    self.px=self.rect.centerx
    self.py=self.rect.centery
   
    
  def tick(self):
    self.px=self.rect.centerx
    self.py=self.rect.centery 
  
  def returnType(self):
    return 'Coin'

  def offscreen(self):  
    # check whether offscreen 
    if self.px >640 or self.py > 480 or self.px < 0 or self.py <0:
      return True
    else: False

# live bar of car
class Livebar(pygame.sprite.Sprite):
  def __init__(self, boss):
    pygame.sprite.Sprite.__init__(self)
    self.boss = boss
    self.image = pygame.Surface((self.boss.rect.height,7))
    self.image.set_colorkey((250,250,250)) # gret transparent
    pygame.draw.rect(self.image, (0,255,0), (0,0,self.boss.rect.height,7),1)
    self.rect = self.image.get_rect()
    self.oldpercent = 0
    #self.bossnumber = self.boss.number # the unique number (name) of my boss
        
  def update(self, time):
    self.percent = self.boss.points / self.boss.fullPoints * 1.0
    if self.percent != self.oldpercent:
      tmp=self.boss.rect.height
      if self.boss.rect.width > self.boss.rect.height:
        tmp=self.boss.rect.width
      pygame.draw.rect(self.image, (250,250,250), (0,0,tmp-2,5)) # fill grey
      pygame.draw.rect(self.image, (0,255,0), (0,0, int(tmp * self.percent),5),0) # fill green
    self.oldpercent = self.percent
    self.rect.centerx = self.boss.rect.centerx
    self.rect.centery = self.boss.rect.centery - self.boss.rect.height /2 - 10
           

class Earth(pygame.sprite.Sprite):
  def __init__(self,gs=None):
    pygame.sprite.Sprite.__init__(self)
    self.gs = gs
    self.image=pygame.image.load("media/globe.png")
    self.size = self.image.get_size()
    self.image = pygame.transform.scale(self.image, (int(self.size[0]*0.5), int(self.size[1]*0.5)))
    self.rect = self.image.get_rect()
    
    self.rotated_image=self.image
    self.orig_image = self.image
    self.px=self.rect.centerx
    self.py=self.rect.centery
    self.points=8000
    self.fullPoints=8000
    self.red=False
    self.explo=False
    self.fragArr=[]
    self.live=Livebar(self)

  def tick(self):
    #print self.points
    self.live.update(0.1)
    if self.points < 150 and self.points > 0: 
      if self.red==False:
        print ('red earth\n')
        self.image=pygame.image.load("media/globe_red100.png")
        self.size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (int(self.size[0]*0.5), int(self.size[1]*0.5)))
        self.rotated_image=self.image
        self.orig_image=self.image
        self.red=True
    elif self.points <= 0:
      if self.explo==False:
        iexplosion=Explosion(self.gs)
        self.gs.explo=iexplosion
        self.explo=True
        pygame.mixer.music.load('media/explode.wav')
        pygame.mixer.music.play(0)
      print ('zero points...earth dies...')
      self.pos=[self.px,self.py]
      
      #for _ in range(random.randint(3,15)):
       #         self.fragArr.append(Fragment(self.pos))
     
    #reduce points when being hitten by lasers
  def points_reduction(self,laserPower):
    self.points-=laserPower



''' earth explosion '''
class Explosion(pygame.sprite.Sprite):
  def __init__(self,gs=None):
    pygame.sprite.Sprite.__init__(self)
    # read images
    self.imageList=dict()
    for i in xrange(0,17,1):
      print (i)
      image="media/explosion/frames0"+str(i).zfill(2)+"a.png"
      self.imageList.update({i:image})
    self.currIndex=0
    self.image=pygame.image.load(self.imageList[self.currIndex])
    self.rect = self.image.get_rect()
    self.rect.center=(550,350)
    self.rotated_image=self.image
    self.orig_image = self.image
    self.counter=0
    self.exploDone=False 
    
  def tick(self):
  
    if self.counter >=3:
      self.currIndex+=1
      self.counter=0
      if self.currIndex <=16:
        self.image=pygame.image.load(self.imageList[self.currIndex])
        self.rotated_image=self.image
        self.orig_image = self.image
      else:
        self.exploDone=True
    else:
      self.counter+=1  


''' car's laser'''
class Laser(pygame.sprite.Sprite):
  def __init__(self,x,y,angle,gs=None):
    pygame.sprite.Sprite.__init__(self)
    self.gs = gs
    self.image=pygame.image.load("media/laser.png")
    self.rect = self.image.get_rect()
    self.rect.center=(x,y)
    self.rotated_image=self.image
    self.orig_image = self.image
    self.px=self.rect.centerx
    self.py=self.rect.centery
    self.dx=7*math.cos(angle)
    self.dy=7*math.sin(angle)
    
  def tick(self):
    self.px=self.rect.centerx
    self.py=self.rect.centery 
    self.rect.center=(self.px+self.dx,self.py+self.dy)
 
  def returnType(self):
    return 'Laser'

  def offscreen(self):  
    # check whether offscreen 
    if self.px >self.gs.width or self.py > self.gs.height or self.px < 0 or self.py <0:
      return True
    else: False


  def earthExplosion(self):
    pass