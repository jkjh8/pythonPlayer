import vlc
import sys, os, socket, struct, json
from PySide2.QtWidgets import QApplication, QWidget, QLabel
from PySide2.QtCore import Slot, Signal, QThread
from PySide2.QtGui import QIcon

class PlayerWindow(QWidget):
    sender = Signal(str)
    def __init__(self):
        super().__init__()
        self.file = None
        self.server = MCAST()
        self.setupUi()

    def setupUi(self):
        self.server.command.connect(self.recv_comm)
        self.sender.connect(self.server.sender)
        
        print('setup Ui')
        self.setWindowIcon(QIcon('logo.png'))
        self.setWindowTitle("Video Player")
        self.setGeometry(100,100,800,450)
        self.show()
        self.server.start()
        self.load_player()
        # self.showFullScreen()
        
    def load_player(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        if sys.platform.startswith('linux'):
            self.player.set_xwidnow(self.winId())
        elif sys.platform.startswith('win32'):
            self.player.set_hwnd(self.winId())
        elif sys.platform.startswith('darwin'):
            self.player.set_nsobject(int(self.winId()))
            
    def load_file(self, file):
        if os.path.isfile(file):
            self.file = file
            media = self.instance.media_new(file)
            self.player.set_media(media)
            self.event_manager = self.player.event_manager()
            self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.finished)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.get_media_length)
            self.event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.play_time_change)
            self.sender.emit(json.dumps({"type":"info","message":'the file loaded successfully{}'.format(file)}))
        else:
            self.sender.emit(json.dumps({"type":"error","message":"the file does not exist"}))
            
    def play(self):
        if self.file != None:
            self.player.play()
            self.sender.emit(json.dumps({"type":"play","media":self.file}))
        else:
            self.sender.emit(json.dumps({"type":"error","message":"dose not load file"}))
            
    def finished(self, _event):
        self.sender.emit(json.dumps({"type":"end"}))
        
    def get_media_length(self, event):
        self.sender.emit(json.dumps({"type":"mediaLength","length":self.player.get_length()}))
    
    def play_time_change(self, event):
        # print(self.player.u.new_time)
        self.sender.emit(json.dumps({"type":"playTime","current":self.player.get_time(),"position":self.player.get_position()}))
        

    @Slot(str)
    def recv_comm(self, data):
        print(data)
        self.sender.emit(data)
        self.data = json.loads(data)
        self.load_file('5.mp4')
        self.player.play()
        
        
    def setFullScreen(self):
        self.showFullScreen()
        
    def setNomalScreen(self):
        self.showNormal()
        
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
    