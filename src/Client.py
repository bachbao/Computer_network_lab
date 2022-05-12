from tkinter import ttk
import tkinter as tk
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

		# Create Setup button
		self.setup = ttk.Button(
			self.master,
			text="SETUP",
			command=self.setupMovie
		)
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button
		self.play = ttk.Button(
			self.master,
			text="PLAY",
			command=self.playMovie
		)
		self.play.grid(row=1, column=1, padx=2, pady=2)
		
		# # Create Pause  button
		self.pause = ttk.Button(
			self.master,
			text="PAUSE",
			command=self.playMovie
		)
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# # Create Teardown button
		self.teardown = ttk.Button(
			self.master,
			text="TEAR",
			command=self.playMovie
		)
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		
		self.label = ttk.Label(
			self.master,
			padding=5
		)
		self.label.grid(row=0, column=0, columnspan=2, sticky="nsew")
		
	
	def setupMovie(self):
		"""Setup button handler."""
		if (self.state != self.INIT):
			print("Not in INIT state!")
		else:
			self.sendRtspRequest(self.SETUP)

	def exitClient(self):
		"""Teardown button handler."""
		if (self.state != self.PLAYING and self.state != self.READY):
			print("Not in PLAYING or READY state!")
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
		if (self.state != self.READY):
			print("Not in READY state!")
		else:
			self.sendRtspRequest(self.PLAY)

	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			data = self.rtpSocket.recv(256)
			# TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		
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
					self.onSetupResponse(session)
				elif self.requestSent == self.PLAY:
					self.onPlayResponse()
				elif self.requestSent == self.PAUSE:
					self.onPauseAccepted()
				elif self.requestSent == self.TEARDOWN:
					self.onTearDownAccepted()
		else:	# negative response from server
			print(f"Oops from server: status<{status}> at seq<{seq}> in session<{session}>")

	def onSetupResponse(self, sessionId: int):
		if (self.sessionId != 0):
			print(f"Error: session ID has not been reseted to 0")
			self.sessionId = 0
		else:
			self.sessionId = sessionId
			self.openRtpPort()
			self.state = self.READY
	
	def onPlayResponse(self):
		self.state = self.PLAYING
	
	def onPauseAccepted(self):
		self.state = self.READY
	
	def onTearDownAccepted(self):
		self.state = self.INIT
		self.sessionId = 0

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
		self.client_socket.close()
		if (hasattr(self, "rtpSocket")):
			self.rtpSocket.close()
		self.master.quit()
