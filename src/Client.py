from tkinter import Tk, ttk
import tkinter as tk
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import io
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	INFO = 3
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	DESCRIBE = 4
	
	# Initiation..
	def __init__(self, master: tk.Tk, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		self.master.geometry("600x400")

		# frame attributes
		self.frame = None

		# Addtional attributes for statistic
		self.RtpLossRate = 0
		self.vidDataRate = 0
		self.fpsRate = 0
		self.flagFirstRecv = False
		self.savedTimestamp = 0
		self.savedRtpseq = 0
		self.lossCounter = 0
		self.dataCounter = 0
		self.framCounter = 0

		# create a label to display statistic
		self.statLabel = ttk.Label(
			self.master,
			padding=5,
			anchor='center',
			text=self.getStatisticString()
		)
		self.statLabel.pack(fill='x')

		# Create a label to display the movie
		self.label = ttk.Label(
			self.master,
			padding=5,
			background='black',
			anchor='center',
			foreground = 'white',
			justify = tk.CENTER,
			compound='none',
			text=self.getDefaultString()
		)
		self.label.pack(expand=True, fill='both')
		
		# Create Play button
		self.play = ttk.Button(
			self.master,
			text="PLAY",
			command=self.playMovie
		)
		self.play.pack(expand=True, fill='both',side='left', ipady=10)
		
		# Create Pause  button
		self.pause = ttk.Button(
			self.master,
			text="PAUSE",
			command=self.pauseMovie
		)
		self.pause.pack(expand=True, fill='both', side='left', ipady=10)
		
		# Create Stop button
		self.teardown = ttk.Button(
			self.master,
			text="STOP",
			command=self.exitClient
		)
		self.teardown.pack(expand=True, fill='both', side='left', ipady=10)

		# Create Describe button
		self.describe = ttk.Button(
			self.master,
			text="DESCRIBE",
			command=self.describeSession
		)
		self.describe.pack(expand=True, fill='both', side='left', ipady=10)

	def exitClient(self):
		"""Teardown button handler."""
		if (self.state != self.PLAYING and self.state != self.READY and self.state != self.INFO):
			print("Not in PLAYING or READY or INFO state!")
		else:
			self.sendRtspRequest(self.TEARDOWN)

	def pauseMovie(self):
		"""Pause button handler."""
		if (self.state != self.PLAYING):
			print("Not in PLAYING state!")
		else:
			self.sendRtspRequest(self.PAUSE)

	def playMovie(self):
		"""Play button handler."""
		if (self.state != self.READY and self.state != self.INIT and self.state != self.INFO):
			print("Not in READY or INIT state!")
		else:
			if (self.state == self.INIT):
				self.sendRtspRequest(self.SETUP)
			self.sendRtspRequest(self.PLAY)
	
	
	def describeSession(self):
		if (self.state == self.INIT):
			print("Play some video to get session description!")
		elif (self.state == self.INFO):
			self.sendRtspRequest(self.PLAY)
		else:
			if (self.state == self.PLAYING):
				self.sendRtspRequest(self.PAUSE)
			self.sendRtspRequest(self.DESCRIBE)

	def listenRtp(self):
		"""Listen for RTP packets."""
		while True:
			if (self.teardownAcked == 1):
				self.onTearDownAcked()
				break
			if (self.state == self.PLAYING):
				try:
					data = self.rtpSocket.recv(16000)
					if data:
						rtpPacket = RtpPacket()
						rtpPacket.decode(data)
						self.computeStatistic(rtpPacket)
						self.writeFrame(rtpPacket.getPayload())
						self.updateMovie(self.frame)
				except socket.timeout:
					pass # delay in streaming
	
	def computeStatistic(self, rtpPacket: RtpPacket):
		if not self.flagFirstRecv:
			self.flagFirstRecv = True
			self.savedTimestamp = rtpPacket.timestamp()
			self.savedRtpseq = rtpPacket.seqNum()
		else:
			if rtpPacket.timestamp() - self.savedTimestamp >= 1:
				self.vidDataRate = self.dataCounter / 1000
				self.RtpLossRate = int(float(self.lossCounter/(rtpPacket.seqNum() - self.savedRtpseq))*100)
				self.fpsRate = self.framCounter
				self.statLabel['text'] = self.getStatisticString()
				self.flagFirstRecv = False
				self.framCounter = 0
				self.lossCounter = 0
				self.dataCounter = 0
			else:
				self.dataCounter += len(rtpPacket.getPayload())
				self.framCounter += 1
				if rtpPacket.seqNum() != self.frameNbr + 1:
					self.lossCounter += rtpPacket.seqNum() - self.frameNbr
		self.frameNbr = rtpPacket.seqNum()
	
	def getDefaultString(self) -> str:
		return "Hit PLAY button"

	def getStatisticString(self) -> str:
		return f"Data rate: {self.vidDataRate}kB/s | Loss rate: {self.RtpLossRate}% | FPS: {self.fpsRate}"

	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		self.frame = ImageTk.PhotoImage(Image.open(io.BytesIO(data)))

	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		self.label['image']=imageFile
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.settimeout(1.0)	# the server should respond within 1 second
		try:
			self.client_socket.connect((self.serverAddr, self.serverPort))
		except socket.timeout:
			print(f"Cannot connect to server at ({self.serverAddr}, {self.serverPort})")
			exit(1)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		self.rtspSeq += 1
		if requestCode == self.SETUP:
			msg = 'SETUP ' + str(self.fileName) + ' RTSP/1.0\nCSeq: ' + str(
				self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
			self.requestSent = self.SETUP
		elif requestCode == self.PLAY:
			msg = 'PLAY ' + str(self.fileName) + ' RTSP/1.0\nCSeq: ' + str(
				self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PLAY
		elif requestCode == self.PAUSE:
			msg = 'PAUSE ' + str(self.fileName) + ' RTSP/1.0\nCSeq: ' + str(
				self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PAUSE
		elif requestCode == self.TEARDOWN:
			msg = 'TEARDOWN ' + str(self.fileName) + ' RTSP/1.0\nCSeq: ' + str(
				self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.TEARDOWN
		elif requestCode == self.DESCRIBE:
			msg = f"DESCRIBE {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"
			self.requestSent = self.DESCRIBE
		else:
			msg = 'Unknown request code'
			self.requestSent = -1
		print("[Client sent:]\n" + msg + "\n-----------------")
		self.client_socket.send(msg.encode())
		self.recvRtspReply()
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		try:
			data = self.client_socket.recv(256)
			if data:
				print("[Data received:]\n" + data.decode("utf-8") + "\n-----------------")
				self.parseRtspReply(data.decode("utf-8"))
		except socket.timeout:
			print("Error: server took to long to respond!")

	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		# process payload
		lines = data.split('\n')
		status = int(lines[0].split(' ')[1])
		seq = int(lines[1].split(' ')[1])
		session = int(lines[2].split(' ')[1])

		# process reply
		if status == 200:	# green light from server
			if (self.rtspSeq != seq):
				print(f"Sequence conflict: clientSeq<{self.rtspSeq}> vs. serverSeq<{seq}>")
			elif (self.requestSent != self.SETUP and self.sessionId != session):
				print(f"SessionId conflict: clientId<{self.sessionId}> vs. serverId<{session}>")
			else:
				if self.requestSent == self.SETUP:
					self.onSetupAccepted(session)
				elif self.requestSent == self.PLAY:
					self.onPlayAccepted()
				elif self.requestSent == self.PAUSE:
					self.onPauseAccepted()
				elif self.requestSent == self.TEARDOWN:
					self.onTearDownAccepted()
				elif self.requestSent == self.DESCRIBE:
					info = lines[3].split(' ')
					self.onDescribeAccepted(info[1], info[2])
		else:	# negative response from server
			print(f"Oops from server: status<{status}> at seq<{seq}> in session<{session}>")

	def onSetupAccepted(self, sessionId: int):
		if (self.sessionId != 0):
			print(f"Error: session ID has not been reseted to 0")
			self.sessionId = 0
		else:
			self.sessionId = sessionId
			self.openRtpPort()
			self.playJob = threading.Thread(target=self.listenRtp)
			self.playJob.daemon = True
			self.playJob.start()
			self.state = self.READY
	
	def onPlayAccepted(self):
		self.label['compound'] = 'none'
		self.state = self.PLAYING
	
	def onPauseAccepted(self):
		self.state = self.READY
	
	def onTearDownAccepted(self):
		self.teardownAcked = 1
		self.state = self.INIT
	
	def onTearDownAcked(self):
		self.frameNbr = 0					# reset frame number
		self.label['text']="Hit PLAY button"	# reset info
		self.label['compound'] = 'text'			# reset compound
		self.rtpSocket.close()			# close RTP socket
		self.sessionId = 0				# reset session ID
		self.teardownAcked = 0			# reset teardown ack
		
		# reset statistic states
		self.RtpLossRate = 0
		self.vidDataRate = 0
		self.flagFirstRecv = False
		self.savedTimestamp = 0
		self.savedRtpseq = 0
		self.lossCounter = 0
		self.dataCounter = 0
		self.framCounter = 0
		self.fpsRate = 0
		self.statLabel['text'] = self.getStatisticString()

	def onDescribeAccepted(self, protocol, encoding):
		self.label['text'] = f"Protocol: {protocol}\nEncoding: {encoding}"
		self.label['compound'] = 'text'
		self.state = self.INFO
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		# Bind the socket object to the rtpPort
		self.rtpSocket.bind(('', self.rtpPort))
		print(f"RTP port is ready at {self.rtpPort}")
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		if (self.state != self.INIT):
			self.sendRtspRequest(self.TEARDOWN)
		self.client_socket.close()
		self.master.quit()
