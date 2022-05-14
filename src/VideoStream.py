class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)			
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data
		
	## Extension ##
	def totalFrame(self):
		totalFrame = 0
		self.fileCopy = open(self.filename, 'rb')
		while True:
			frameLength = self.fileCopy.read(5)
			if frameLength:
				self.fileCopy.read(int(frameLength))
				totalFrame += 1
			else:
				self.fileCopy.close()
				break
		return totalFrame
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	