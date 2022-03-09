import vlc
import sys, os, socket, struct, json, logging, copy
from PySide2.QtWidgets import QApplication, QWidget, QLabel
from PySide2.QtCore import Slot, Signal, QThread
from PySide2.QtGui import QIcon

class PlayerWindow(QWidget):
    sender = Signal(str)
    def __init__(self):
        super().__init__()
        self.player = None
        self.file = None
        self.server = MCAST()
        self.instance = vlc.Instance()
        self.setupUi()

    def setupUi(self):
        self.server.command.connect(self.recv_comm)
        self.sender.connect(self.server.sender)
        
        logging.debug('setup ui winddow')
        self.setWindowIcon(QIcon('logo.png'))
        self.setWindowTitle("Video Player")
        self.setGeometry(100,100,800,450)
        self.show()
        self.server.start()
        # self.load_player()
        # self.showFullScreen()
        
    def rt(self, kwargs):
        msg = kwargs.copy()
        if not "type" in kwargs:
            msg["type"] = "info"
        if not "result" in kwargs:
            msg["result"] = True
        if not "file" in kwargs:
            msg["file"] = self.file
        self.sender.emit(json.dumps(msg))
        
    def set_window(self):
        if sys.platform.startswith('linux'):
            self.player.set_xwidnow(self.winId())
            logging.info('player window loaded on linux')
            self.rt({
                "command":"load_player",
                "message":"player load on linux",
                "os":"linux"
            })
        elif sys.platform.startswith('win32'):
            self.player.set_hwnd(self.winId())
            logging.info('player window loaded on win32')
            self.rt({
                "command":"load_player",
                "message":"player load on windows",
                "os":"win32"
            })
        elif sys.platform.startswith('darwin'):
            self.player.set_nsobject(int(self.winId()))
            logging.info('player window loaded on darwin')
            self.rt({
                "command":"load_player",
                "message":"player load on macos",
                "os":"darwin"
            })
        else:
            logging.error("player window load failed")
            self.rt({
                "type":"error",
                "command":"load_player",
                "result":False,
                "message":"player load failed",
            })
        
    def load_player(self):
        if self.player == None:
            self.player = self.instance.media_player_new()
            
    def load_file(self, file):
        # 파일 교체전 정지
        self.load_player()
        # 파일 학인후 교체
        if os.path.isfile(file):
            self.file = file
            media = self.instance.media_new(file)
            self.player.set_media(media)
            self.set_window()
            
            self.setWindowTitle("Video Player {}".format(self.file))
            logging.info("file loaded {}".format(file))
            
            # set event manager
            self.event_manager = self.player.event_manager()
            self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.finished)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.get_media_length)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.play_time_change)
            
            self.rt({
                "command":"load",
                "message":"the file loaded successfully"
            })
        else:
            logging.error("file dose not exist {}".format(file))
            self.rt({
                "type":"error",
                "command":"load",
                "result":False,
                "message":"the file does not exist"
            })
            
    def play(self):
        if self.file != None:
            self.player.play()
            self.rt({
                "command":"play"
            })
        else:
            self.rt({"type":"error","message":"dose not load file"})

    def stop(self):
        try:
            self.player.stop()
            self.setWindowTitle("Video Player")
            self.rt({
                "command":"stop",
                "message":"player stopped successfully"
            })
            self.file = None
        except Exception as e:
            self.rt({
                "type":"error",
                "command":"stop"
            })
            pass
        
    def set_position(self, value):
        try:
            self.player.set_position(value)
            self.rt({
                "command":"setposition",
                "value": value
            })
        except:
            self.rt({
                "type":"error",
                "command":"setopsition",
                "result":False
            })
            pass
        
    def setFullScreen(self, value):
        try:
            self.player.set_fullscreen(value)
            if value == True:
                self.showFullScreen()
            else:
                self.showNormal()
            self.rt({
                "command":"fullscreen",
                "fullscreen":self.isFullscreen()
            })
        except:
            self.rt({
                "type":"error",
                "command":"fullscreen",
                "result":False
            })
            pass
    
    def getStatus(self):
        try:
            self.rt({
                "command":"status",
                "fullscreen":self.isFullscreen(),
                "status":str(self.player.get_state()),
                "inplaying":self.player.is_playing(),
                "volume":self.player.audio_get_volume(),
                "scale":self.player.video_get_scale(),
                "current":self.player.get_time(),
                "position":round(self.player.get_position(),3),
                "rate": self.player.get_rate(),
                "mute":self.player.audio_get_mute()
            })
        except Exception as e:
            print(e)
            self.rt({
                "type":"error",
                "command":"status",
                "result":False
            })
            pass
   
        
    # player callback event  
    def finished(self, _event):
        self.setWindowTitle("Video Player")
        self.rt({
            "command":"finished",
            "message":"play ended successfully",
        })
        
    def get_media_length(self, event):
        self.rt({
            "command":"length",
            "length":self.player.get_length()
        })
    
    def play_time_change(self, event):
        self.rt({
            "command":"currentTime",
            "current":self.player.get_time(),
            "position":round(self.player.get_position(),3)
        })
        
     
        
    @Slot(str)
    def recv_comm(self, data):
        self.data = json.loads(data)
        if self.data["command"] == "play":
            if "file" in self.data:
                self.load_file(self.data["file"])
            self.play()
        elif self.data["command"] == "stop":
            self.player.stop()
        elif self.data["command"] == "load":
            self.load_file(self.data["file"])
        elif self.data["command"] == "fullscreen":
            self.setFullScreen(self.data['value'])
        elif self.data["command"] == "status":
            self.getStatus()
        elif self.data["command"] == "setposition":
            self.set_position(self.data["value"])
        else:
            self.rt({
                "type":"error",
                "result":False,
                "command":"net",
                "message":"unknown command"
            })
        
class MCAST(QThread):
    command = Signal(str)
    def __init__(self, parent=None):
        super(MCAST, self).__init__(parent)
        self.addr = "224.12.123.234"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self.sock.bind(('',12302))
        
        group = socket.inet_aton(self.addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print('open multicast server')
    
    def run(self):
        while True:
            try:
                data, address = self.sock.recvfrom(2048)
                self.command.emit(data.decode('utf-8'))
            except Exception as e:
                print(e)
                pass
            
    @Slot(str)
    def sender(self, data):
        self.sock.sendto(data.encode('utf-8'), (self.addr, 12300))

if __name__=="__main__":
    app = QApplication(sys.argv)
    main = PlayerWindow()
    sys.exit(app.exec_())

# send_port = 12300
# recv_port = 12302
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# def start_server():
#     sock.bind(("127.0.0.1", recv_port))
#     print('Start UDP Server ',sock)
#     while True:
#         try:
#             data, addr = sock.recvfrom(2048)
#             data = data.decode('utf-8')
#             print("recv : " + data)
#             if 'load' in data:
#                 player.load_file('5.mp4')
#             elif 'play' in data:
#                 player.play()
#         except Exception as e:
#             print('error recv', e)
#             # sender(json.dumps({"type":"error","message": "network error"}))
#             pass
                    
# def sender(data):
#     try:
#         print('send data', data)
#         sock.sendto(data.encode('utf-8'), ("127.0.0.1", send_port))
#     except Exception as e:
#         print(e)
#         pass
        
# class Player(threading.Thread):
#     def __init__(self):
#         self.load_player()
#         self.file = None
#         print("플레이어 활성화")
#         super(Player, self).__init__()
        
#     def load_player(self):
#         self.instance = vlc.Instance()
#         self.player = self.instance.media_player_new()
#         self.player.set_hwnd(0)
        
#     def load_file(self, file):
#         if os.path.isfile(file):
#             self.file = file
#             media = self.instance.media_new(file)
#             self.player.set_media(media)
#             self.event_manager = self.player.event_manager()
#             self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.finished)
#             self.event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.get_media_length)
#             self.event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.play_time_change)
#             sender(json.dumps({"type":"info","message":'the file loaded successfully{}'.format(file)}))
#         else:
#             sender(json.dumps({"type":"error","message":"the file does not exist"}))
            
#     def play(self):
#         if self.file != None:
#             self.player.play()
#             sender(json.dumps({"type":"play","media":self.file}))
#         else:
#             sender(json.dumps({"type":"error","message":"dose not load file"}))
            
#     def finished(self, _event):
#         sender(json.dumps({"type":"end"}))
        
#     def get_media_length(self, event):
#         sender(json.dumps({"type":"mediaLength","length":self.player.get_length()}))
    
#     def play_time_change(self, event):
#         # print(self.player.u.new_time)
#         sender(json.dumps({"type":"playTime","current":self.player.get_time(),"position":self.player.get_position()}))
    

# if __name__=="__main__":
#     player = Player()
#     player.setDaemon(True)
#     player.start()
#     start_server()
    