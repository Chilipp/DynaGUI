# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 15:59:21 2019

@author: controlroom [benjamin bolling]
"""
try:
    import PyQt5.QtWidgets as QtGui
    from PyQt5 import QtCore
except:
    from PyQt4 import QtCore, QtGui

import PyTango as PT
import time
import sys
class Dialog(QtGui.QDialog):
    def __init__(self, inp):
        QtGui.QDialog.__init__(self)
        if inp == 0:
            loadflag = 0
        else:
            try:
                self.loadfile(inp,1)
                self.Nrows
                loadflag = 1
            except:
                loadflag = 0
        if loadflag == 0:
            # All device attributes needed (basically which can be TRUE or False)
            self.listofbpmattributes = ['AGCEnabled',
                                   'ADCEnabled',
                                   'EnableADC',
                                   'InterlockEnabled',
                                   'Interlock_Enabled',
                                   'Attribute1',
                                   'Attribute2',
                                   'Attribute3',
                                   'StatusOpen',
                                   'StatusClosed',
                                   'OutputOn']
            
            # Some list of devices. List 3 consists of some random stuff
            self.devlist = ['r1-101/dia/bpm-02',
                     'i-s01b/dia/bpl-01',
                     'i-s04b/dia/bpl-01',
                     'r3-301l/dia/bpm-01',
                     'i-s19b/dia/bpl-01',
                     'r1-109/dia/bpm-03',
                     'i-s01a/vac/vgmb-01',
                     'i-s03a/vac/vgmb-01',
                     'r3-a110711cab08/mag/pspi-02']
            self.Nrows = 20
        self.reloadflag = 0
        self.showallhideflag = False
        
        self.setWindowTitle("DynaGUI TF")
        
        # Construct the toplayout and make it stretchable
        self.toplayout = QtGui.QVBoxLayout(self)
        self.toplayout.addStretch()
        
        # Construct the combobox for the list of attributes
        self.listofbpmattributeslistbox = QtGui.QComboBox(self)
        self.listofbpmattributeslistbox.addItems(self.listofbpmattributes)
        self.listofbpmattributeslistbox.currentIndexChanged.connect(self.statuscheck)
        self.toplayout.addWidget(self.listofbpmattributeslistbox)
        
        # Here we add a button that sets the selected attribute as TRUE for all the BPM:s in the selected ring
        self.enableallbutton = QtGui.QPushButton("Enable all")
        self.enableallbutton.clicked.connect(self.enableallbuttonclicked)
        self.enableallbutton.hide()
        
        # Construct the button for setting up a dynamic list of attributes
        self.listbtn = QtGui.QPushButton("Edit DynaGUI")
        self.listbtn.clicked.connect(self.listbtnclicked)
        self.listbtn.setEnabled(True)
        self.toplayout.addWidget(self.listbtn)
        
        # Now we construct the sublayout which will consist of the dynamically constructed buttons of the lists defined above (in example; list1 or list2)
        self.sublayout = QtGui.QGridLayout()
        self.toplayout.addLayout(self.sublayout)
        
        # Now we construct a groupbox for all the dynamically constructed buttons. Edit its text to whatever is appropriate. Then its added to the sublayout.# Now we construct the sublayout which will consist of the dynamically constructed buttons of the lists defined above (in example; list1 or list2)
        self.groupBox = QtGui.QGroupBox()
        self.sublayout.addWidget(self.groupBox)
        self.sublayout = QtGui.QGridLayout(self.groupBox)
        
        # Construct a simple label widget which in this example has the purpose of displaying various messages to the user (status messages)
        self.bottomlabel = QtGui.QLabel("")
        self.toplayout.addWidget(self.bottomlabel)
        
        # Construct a horizontal layout box for the load and save buttons (must be a sublayer of the toplayout)
        self.loadsavewdg = QtGui.QWidget(self)
        self.toplayout.addWidget(self.loadsavewdg)
        self.horizlayout = QtGui.QHBoxLayout(self.loadsavewdg)
        
        # Construct the load and save buttons, connect them to their functions and add them to their horizontal container
        self.loadbtn = QtGui.QPushButton("Load")
        self.savebtn = QtGui.QPushButton("Save")
        self.loadbtn.clicked.connect(self.loadbtnclicked)
        self.loadbtn.setShortcut("Ctrl+o")
        self.loadbtn.setToolTip("Load a configuration (ctrl+o).")
        self.savebtn.clicked.connect(self.savebtnclicked)
        self.savebtn.setShortcut("Ctrl+s")
        self.savebtn.setToolTip("Save a configuration (ctrl+s).")
        self.horizlayout.addWidget(self.loadbtn)
        self.horizlayout.addWidget(self.savebtn)
        
        # Now we create a button to update the status selected in the combobox for all the dynamically constructed buttons
        self.updatebutton = QtGui.QPushButton("Update statuses")
        self.updatebutton.clicked.connect(self.statuscheck)
        self.toplayout.addWidget(self.updatebutton)
        self.toplayout.addWidget(self.enableallbutton)
        
        # Run the script for generating the dynamical buttons
        self.getallDevs()
        
    def savebtnclicked(self):
        nameoffile = QtGui.QFileDialog.getSaveFileName(self, 'Save to File')
        if not nameoffile:
            self.bottomlabel.setText("Cancelled save configuration.")
        else:
            file = open(nameoffile, 'w')
            self.toSave = str('IamaDynaGUIfile' + '\n' + "##IamYourSeparator##\n" + '\n'.join(self.devlist) + '\n' + "##IamYourSeparator##\n" + '\n'.join(self.listofbpmattributes) + '\n' + "##IamYourSeparator##\n" + str(self.Nrows))
            file.write(self.toSave)
            file.close()
            self.bottomlabel.setText("Configuration saved to file.")
            self.bottomlabel.setToolTip("Saved configuation to file: "+nameoffile)
        
    def loadbtnclicked(self):
        nameoffile = QtGui.QFileDialog.getOpenFileName(self, 'Load File')
        if not nameoffile:
            self.bottomlabel.setText("Cancelled loading configuration.")
        else:
            self.loadfile(nameoffile,0)
            
    def loadfile(self,nameoffile,inp2):
            print(nameoffile)
            file = open(nameoffile, 'r')
            splitToLoad = file.read()
            splitToLoad = splitToLoad.split("##IamYourSeparator##")
            identifier = splitToLoad[0].split('\n')
            while("" in identifier): # Get rid of empty strings
                identifier.remove("")
            if identifier[0] == 'IamaDynaGUIfile':
                print("Identified as a DynaGUI file.")
                try:
                    devlist = splitToLoad[1].split("\n")
                    while("" in devlist): # Get rid of empty strings
                        devlist.remove("")
                    listofbpmattributes = splitToLoad[2].split("\n")
                    while("" in listofbpmattributes): # Get rid of empty strings
                        listofbpmattributes.remove("")
                    Nrows = splitToLoad[3].split("\n")[1]
                    self.devlist = devlist
                    self.listofbpmattributes = listofbpmattributes
                    self.Nrows = float(Nrows)
                    # Destroy the current buttons.
                    if inp2 == 0:
                        self.listofbpmattributeslistbox.clear()
                        self.listofbpmattributeslistbox.addItems(self.listofbpmattributes)
                        self.bottomlabel.setText("Loaded configuration.")
                        self.killdynamicbuttongroup()
                        self.resize(10,10)
                        # All buttons are gone, so lets construct the new buttons.
                        self.getallDevs()
                        # The layout should be minimal, so make it unrealistically small (x=10, y=10 [px]) and then resize to minimum.
                        self.setMaximumSize(10,10)
                        #self.resize(self.sizeHint().width(), self.sizeHint().height())
                        self.bottomlabel.setToolTip("Loaded configuration from file: "+nameoffile)
                except:
                    if inp2 == 0:
                        self.bottomlabel.setText("Conf. file error: Missing separator(s).")
            else:
                if inp2 == 0:
                    self.bottomlabel.setText("Not a DynaGUI file - missing identifier.")
    
    def enableallbuttonclicked(self):
        for item in self.buttonGroup.buttons():
            proxy = item.text()
            prox=[PT.DeviceProxy(str(proxy))]
            
            # Get the states of all devices, one at a time (val)
            for dev in prox:
                try:
                    val = dev.read_attribute(str(self.listofbpmattributeslistbox.currentText())).value
                    
                    # Try to write to the device
                    if val is False: # If false, interlock is disabled.
                        dev.write_attribute(str(self.listofbpmattributeslistbox.currentText()),True)
                except:
                    item.setStyleSheet('background-color: fuchsia')
        self.statuscheck()
    
    def killdynamicbuttongroup(self):
        # Destroy / kill all buttons currently constructed in the buttongroup.
        self.bottomlabel.setText(str("Loading " + str(self.listofbpmattributeslistbox.currentText()) + " statuses..."))
        for i in reversed(range(self.sublayout.count())):
            item = self.sublayout.itemAt(i)
            if isinstance(item, QtGui.QWidgetItem):
                item.widget().close()        

    def getallDevs(self):
        # Construct all necessary buttons
        self.BPMproxies = self.devlist
        
        rowcount = -1
        colcount = 0
        
        # Here the construction begins for all the pushbuttons, and we make them all belong to the groupbox.
        for index in self.BPMproxies:
            rowcount += 1
            button = QtGui.QPushButton(index, self.groupBox)
            self.sublayout.addWidget(button,rowcount,colcount,1,1)
            self.groupBox.setStyleSheet("text-align:center")
            if rowcount == self.Nrows - 1:
                rowcount = -1
                colcount += 1
        
        # Here we construct the buttongroup.
        self.buttonGroup = QtGui.QButtonGroup(self)
        self.buttonGroup.buttonClicked.connect(self.handleButtonClicked)
        
        # Here we add all buttons to the buttongroup.
        for button in self.groupBox.findChildren(QtGui.QPushButton):
            if self.buttonGroup.id(button) < 0:
                self.buttonGroup.addButton(button)
        
        # Get the statuses
        self.statuscheck()
        
    def statuscheck(self):
        for item in self.buttonGroup.buttons():
            try:
                proxy = item.text()
                prox = [PT.DeviceProxy(str(proxy))]
                try:
                    for bd in prox:
                        val = bd.read_attribute(str(self.listofbpmattributeslistbox.currentText())).value
                        if val is True:
                            item.setStyleSheet('background-color: lime')
                        elif val is False:
                            item.setStyleSheet('background-color: red')
                except:
                    item.setStyleSheet('background-color: fuchsia')
            except:
                item.setStyleSheet('QPushButton {background-color: maroon; color: white}')
        self.bottomlabel.setText(str(str(self.listofbpmattributeslistbox.currentText()) + " statuses loaded."))
        
    def handleButtonClicked(self,button):
        for item in self.buttonGroup.buttons():
            if button is item:
                proxy = item.text()
                prox=[PT.DeviceProxy(str(proxy))]
                for dev in prox:
                    try:
                        val = dev.read_attribute(str(self.listofbpmattributeslistbox.currentText())).value
                        if val is True: # If true --> Interlock is enabled.
                            dev.write_attribute(str(self.listofbpmattributeslistbox.currentText()),False)
                        if val is False: # If true --> Interlock is disabled.
                            dev.write_attribute(str(self.listofbpmattributeslistbox.currentText()),True)
                        time.sleep(0.5)
                        val2 = dev.read_attribute(str(self.listofbpmattributeslistbox.currentText())).value
                        if val2 is True:
                            item.setStyleSheet('background-color: lime')
                        elif val2 is False:
                            item.setStyleSheet('background-color: red')
                    except:
                        item.setStyleSheet('background-color: fuchsia')
            
    def listbtnclicked(self):
        listGui = listbtnGUI(self)
        listGui.setModal(True)
        listGui.exec_()
        self.listofbpmattributeslistbox.clear()
        self.listofbpmattributeslistbox.addItems(self.listofbpmattributes)
        if self.showallhideflag is True:
            self.enableallbutton.show()
        elif self.showallhideflag is False:
            self.enableallbutton.hide()
        
        if self.reloadflag == 1:
            print("Reload")
            self.killdynamicbuttongroup()
            self.getallDevs()
            self.reloadflag = 2
            
        if self.reloadflag == 2:
            # The layout should be minimal, so make it unrealistically small (x=10, y=10 [px]) and then resize to minimum.
            self.setMaximumSize(10,10)
            self.resize(self.sizeHint().width(), self.sizeHint().height())
            self.reloadflag = 0

class listbtnGUI(QtGui.QDialog):
    def __init__(self, parent = Dialog):
        super(listbtnGUI, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("Edit DynaGUI TF")
        listgui = QtGui.QFormLayout(self)
        
        devslbl = QtGui.QLabel("List of devices::")
        self.textboxDevs = QtGui.QPlainTextEdit('\n'.join(parent.devlist))
        
        attrlbl = QtGui.QLabel("List of device attributes:")
        self.textboxAttr = QtGui.QPlainTextEdit('\n'.join(parent.listofbpmattributes))
        
        rowslbl = QtGui.QLabel("Max. number of rows:")
        self.textboxRows = QtGui.QSpinBox()
        self.textboxRows.setValue(parent.Nrows)
        
        self.showhideenableallbtn = QtGui.QCheckBox("Show the 'Enable All' button")
        self.showhideenableallbtn.setChecked(parent.showallhideflag)
        
        okbtn = QtGui.QPushButton('Ok')
        nobtn = QtGui.QPushButton('Cancel')
        listgui.addRow(devslbl)
        listgui.addRow(self.textboxDevs)
        listgui.addRow(attrlbl)
        listgui.addRow(self.textboxAttr)
        listgui.addRow(rowslbl,self.textboxRows)        
        listgui.addRow(self.showhideenableallbtn)
        listgui.addRow(okbtn, nobtn)
        okbtn.clicked.connect(self.confirmfunc)
        nobtn.clicked.connect(self.cancelfunc)
        
    def confirmfunc(self):
        textDevs = str(self.textboxDevs.toPlainText())
        self.newlistDevs = textDevs.split()
        
        if self.parent.showallhideflag != self.showhideenableallbtn.isChecked():
            self.parent.showallhideflag = self.showhideenableallbtn.isChecked()
            self.parent.reloadflag = 2
        
        if self.parent.devlist != self.newlistDevs:
            self.parent.devlist = self.newlistDevs
            self.parent.reloadflag = 1
        
        textAtts = str(self.textboxAttr.toPlainText())
        self.newlistAtts = textAtts.split()
        self.parent.listofbpmattributes = self.newlistAtts
        
        if self.parent.Nrows != self.textboxRows.value():
            self.parent.Nrows = self.textboxRows.value()
            self.parent.reloadflag = 1
            
        self.close()
    
    def cancelfunc(self):
        self.close()

if __name__ == '__main__':
    try:
        inp = sys.argv[1]
    except:
        inp = 0
    app = QtGui.QApplication(sys.argv)
    window = Dialog(inp)
    window.show()
    sys.exit(app.exec_())
