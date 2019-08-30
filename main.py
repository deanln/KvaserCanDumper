import sys, os
from canlib import canlib
from PyQt4 import QtCore
from PyQt4 import QtGui


class CanDumpThread(QtCore.QThread):
    can_dump = QtCore.pyqtSignal(object)

    def __init__(self):
        # Initialize existence of thread, declare canlib object, open a channel handle (0), set channel parameters
        QtCore.QThread.__init__(self)
        # Create canlib object
        # Print out current canlib driver version to console
        print("CANlib version: " + str(canlib.dllversion()))
        # Open a channel that accepts connected physical CAN device, default to virtual channel if none found
        self.handle1 = canlib.openChannel(0, canlib.canOPEN_ACCEPT_VIRTUAL)
        self.h1data = canlib.ChannelData(0)
        # Print out current channel name and data to console
        print("Using channel: " + str(self.h1data.channel_name) + ", EAN: " + str(self.h1data.card_upc_no))
        # Set the can bus control to normal
        self.handle1.setBusOutputControl(canlib.canDRIVER_NORMAL)
        # Set CAN bit-rate to 125k (GCM default bit-rate)
        self.handle1.setBusParams(canlib.canBITRATE_125K)
        # Turn channel bus ON
        self.handle1.busOn()

        self.actively_dumping = True  # Flag for 'self.run' method

    def run(self):
        # Method is called when .start() is called within QThread class.
        while self.actively_dumping:
            self.can_dump.emit(self.listen_to_can())

    def listen_to_can(self):
        # Reads messages from the channel handler
        try:
            # Call .read() method and return <Tuple> message as a string
            current_msg = self.handle1.read(1000)
            return str(current_msg)
        except canlib.canNoMsg:
            # If .read() returns NoneType, catch exception and keep on listening...
            return str("Listening...")


class CanWindow(QtGui.QWidget):
    # Creates Main Graphical User Interface
    def __init__(self, *args):
        # Initialize a GUI window, declares a new thread for CAN dumping, and sets existence flag for new dump thread
        QtGui.QWidget.__init__(self, *args)
        self.current_thread = CanDumpThread()
        self.thread_exists = False
        self.setWindowTitle("CANbus Dumper")
        self.setFixedSize(340, 360)

        # create PyQt4 objects
        self.picture_label = QtGui.QLabel()
        self.picture_label.setPixmap(QtGui.QPixmap(os.getcwd() + "/logo.png"))
        self.header = QtGui.QLabel("***Kvaser Devices Only***")
        self.header.setAlignment(QtCore.Qt.AlignHCenter)
        self.footer = QtGui.QLabel("To display CAN Dump, press 'Start Dumping'")
        self.start_button = QtGui.QPushButton("Start Dumping")
        self.stop_button = QtGui.QPushButton("Pause")
        self.te = QtGui.QTextEdit()

        # layout PyQt4 objects
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.picture_label)
        layout.addWidget(self.header)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.te)
        layout.addWidget(self.footer)
        self.setLayout(layout)

        # create connection of PyQt4 objects to associated methods
        self.start_button.clicked.connect(self.start_dump)
        self.stop_button.clicked.connect(self.stop_display_dump)

    def start_dump(self):
        # Method to start dumping can data.
        # If CAN Dump thread exists
        if self.thread_exists:
            # Disable start button (FAIL SAFE)
            self.start_button.setEnabled(False)
            # Set appropriate footer text
            self.footer.setText("Press 'Pause' to freeze displayed data.")
            # Connect thread data to display on GUI
            self.current_thread.can_dump.connect(self.display_dump)
        # If CAN dump thread is not initialized
        else:
            # Print out initialization on console
            print("Start CAN Dump")
            # Disable start button (FAIL SAFE)
            self.start_button.setEnabled(False)
            # Set start button to new 'Resume' text
            self.start_button.setText("Resume")
            # Set appropriate footer text
            self.footer.setText("Press 'Pause' to freeze displayed data.")
            # Initialize a new thread object
            self.current_thread.start() # Calling .start() will call self.run() from the QThread class
            # Set boolean flag on existence of thread
            self.thread_exists = True
            # Connect thread data to display on GUI
            self.current_thread.can_dump.connect(self.display_dump)

    def stop_display_dump(self):
        # Disconnects thread data dump from GUI display
        try:
            # Enable the start button
            self.start_button.setEnabled(True)
            # Set appropriate footer text
            self.footer.setText("Press 'Resume' to resume listening.")
            # Disconnect thread data from display on GUI
            self.current_thread.can_dump.disconnect(self.display_dump)
        except TypeError:
            # In the case already disconnected, raise and catch exception.
            self.footer.setText("Already Paused!")

    def display_dump(self, output):
        # Method responsible for printing dump data onto QTextEdit widget
        print(output)  # Print to dump to Python console
        self.te.setText(output)


def main():
    # Main loop
    app = QtGui.QApplication(sys.argv)
    w = CanWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# End
