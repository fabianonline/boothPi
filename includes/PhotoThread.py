class PhotoThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.photo_taken = False

	def set_data(self, filename, number):
		self.filename = filename
		self.number = number
	
	def run(self):
		self.photo_taken = False
		# Take the photo
		reset_usb()
		print("This is take_photo().")
		process = subprocess.Popen("gphoto2 --capture-image-and-download --force-overwrite --filename " + self.filename, stdout=subprocess.PIPE, shell=True)
		while True:
			line = process.stdout.readline()
			if line == '':
				break
			if line.startswith("New file is in"):
				self.photo_taken = True

		global photo_load_threads
		photo_load_threads[self.number-1] = PhotoLoadThread(self.filename, self.number-1)
		photo_load_threads[self.number-1].start()