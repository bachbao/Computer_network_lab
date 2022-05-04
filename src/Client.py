from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
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
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause  button
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
	#TODO
		self.sendRtspRequest(self.SETUP)
	def exitClient(self):
		"""Teardown button handler."""
	#TODO
		self.sendRtspRequest(self.TEARDOWN)
	def pauseMovie(self):
		"""Pause button handler."""
	#TODO
		self.sendRtspRequest(self.PAUSE)
	def playMovie(self):
		"""Play button handler."""
	#TODO
		self.sendRtspRequest(self.PLAY)
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
	#TODO
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.connect((self.serverAddr, self.serverPort))
	
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
		else:
			msg = 'Unknown request code'
			self.requestSent = -1
		print("Client sent: " + msg)
		self.client_socket.send(msg.encode())
		self.recvRtspReply()
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		data = self.client_socket.recv(256)
		if data:
			print("Data received:\n" + data.decode("utf-8"))
			self.parseRtspReply(data.decode("utf-8"))

	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		lines = data.split('\n')
		status = int(lines[0].split(' ')[1])
		seq = int(lines[1].split(' ')[1])
		session = int(lines[2].split(' ')[1])
		if status == 200:
			if self.requestSent == self.SETUP:
				if self.state == self.INIT and self.sessionId == 0 and self.rtspSeq == seq:
					self.state = self.READY
					self.sessionId = session
			elif self.requestSent == self.PLAY:
				if self.state == self.READY and self.sessionId == session and self.rtspSeq == seq:
					self.state = self.PLAYING
			elif self.requestSent == self.PAUSE:
				if self.state == self.PLAYING and self.sessionId == session and self.rtspSeq == seq:
					self.state = self.READY
			elif self.requestSent == self.TEARDOWN:
				if (self.state == self.READY or self.state == self.PLAYING) and self.sessionId == session and self.rtspSeq == seq:
					self.state = self.INIT
					self.sessionId = 0

	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.rtpSocket.bind(('', self.rtpPort))
		print("RTP port is ready ...")
		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		self.client_socket.close()
