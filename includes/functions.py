def quit():
	root.destroy()

def detect_usb():
	print "In detect_usb()"
	result = subprocess.Popen("lsusb", stdout=subprocess.PIPE).stdout.read()
	match = re.search("Bus (\d{3}) Device (\d{3}): ID " + CAMERA_ID, result)
	if match != None:
		result = "/dev/bus/usb/" + match.group(1) + "/" + match.group(2)
		print "Path to USB device: " + result
		return result
	raise "USB Device " + CAMERA_ID + " not found! Check your camera's ID with 'lsusb' and modify CAMERA_ID in photobooth.py."


def check_button_pressed():
	global root
	button_pressed = GPIO.input(12)
	if button_pressed:
		start_run()
	else:
		root.after(5, check_button_pressed)

def start_run():
	global filename_schema
	global canvas
	global h, space
	global line
	global text_offset
	filename_schema = time.strftime("photos/%Y%m%d-%H%M%S---{}.jpg")
	print "h: " + str(h)
	width = space*2+IMAGE_SIZE
	print "width: " + str(width)
	canvas.pack()
	line = 0
	advance_line()

def reset_usb():
	global usb_device
	print "In reset_usb()"
	cmd = os.path.abspath(os.path.dirname(sys.argv[0])) + "/usbreset " + usb_device
	print "Executing: " + cmd
	subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.read()

def display_text(string):
	global canvas
	global text
	canvas.delete(text)
	text = canvas.create_text(w/2, h/2, text=string, fill="#45ADA6", anchor="c", font="Lucida 90", justify=CENTER)

def take_photo(number):
	global photo_thread
	global filename_schema
	photo_thread.set_data(filename_schema.format(number), number)
	photo_thread.run()
	while True:
		print "Warte auf photo_taken..."
		if photo_thread.photo_taken:
			break
		time.sleep(0.1)

def show_overview():
	global photo_load_threads, canvas
	border = 50
	img_size = (h - 3*50) / 2
	canvas.delete(ALL)
	for i in range(4):
		print "Warte auf Nummer " + str(i)
		photo_load_threads[i].join()
		print "Zeige Photo von Nummer " + str(i)
		photo_load_threads[i].show_photo(canvas)

def advance_line():
	global line
	global lines
	if line>=len(lines):
		line = 0
		return
	current_line = lines[line]
	if current_line[1]=="text":
		print("Text: " + current_line[2])
		display_text(current_line[2])
	elif current_line[1]=="photo":
		print("Photo! Nummer " + str(current_line[2]))
		take_photo(current_line[2])
	elif current_line[1]=="overview":
		show_overview()
	elif current_line[1]=="clear":
		global canvas
		canvas.delete(ALL)
	print("Warte: " + str(current_line[0]))
	if line+1<len(lines):
		root.after(current_line[0], advance_line)
	else:
		root.after(1000, check_button_pressed)
	line += 1

def wait_for_button_press():
	global lines
	display_text(lines[len(lines)-1][2])
	root.after(1000, check_button_pressed)

def check_things():
	global usb_device, lines

	# Check the time - if the raspberry has no network connection, it can't get the current
	# time via NTP and it will use January 1st, 1970. We check for this and quit, if this happens.
	if (time.strftime("%Y") == "1970"):
		raise "Current time not set. Please execute 'sudo date -s \"20140726 13:14:55\"' and try again."

	# Kamera
	# detect_usb will raise an error if there is no camera matching CAMERA_ID found.
	usb_device = detect_usb()

	# lines[len(lines)-1][1] == "text"
	if (lines[len(lines)-1][1] != "text"):
		raise "Last Line of lines (in photobooth.py) has to be of type 'text'. It will be used as stand-by text."

	# usbreset
	if (!os.path.isfile("usbreset")):
		raise "'usbreset' not found in the photobooth directory. Compile it by running 'gcc usbreset.c'."

def init():
	global line, root, w, h, space, images, photo_load_threads, canvas, text, filename_schema, photo_thread, usb_device
	check_things()
	line = 0

	root = Tk()
	w, h = root.winfo_screenwidth(), root.winfo_screenheight()
	root.overrideredirect(1)
	root.wm_attributes("-topmost", 1)
	root.focus()
	root.geometry("%dx%d+0+0" % (w, h))

	space = (h-4*IMAGE_SIZE)/5

	images = [None, None, None, None]
	photo_load_threads = [None, None, None, None]

	canvas = Canvas(root, width=w, height=h, bg="Black")
	canvas.pack()

	text = canvas.create_text(w/2, h/2, text="PhotoBooth v"+VERSION, fill="red", anchor="c")

	filename_schema = "photos/this-should-not-happen---{}.jpg"

	photo_thread = PhotoThread()

	GPIO.setup(12, GPIO.IN)

	

	root.focus_set()
	root.bind("<Escape>", quit)
	root.after(2000, wait_for_button_press)
	root.mainloop()
