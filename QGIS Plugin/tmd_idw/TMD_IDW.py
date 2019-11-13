# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TMD_IDW_Class
								 A QGIS plugin
 Interpolation data from TMD
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
							  -------------------
		begin				: 2019-10-28
		git sha			  : $Format:%H$
		copyright			: (C) 2019 by i-bitz
		email				: aaa@gmail.com
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction,QFileDialog,QMessageBox

import os.path,requests ,csv,datetime
from qgis.core import *
from qgis.analysis import *


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .TMD_IDW_dialog import TMD_IDW_ClassDialog


pixel_size=[]

date = str(datetime.date.today())
#date=date.replace("-", '_')






class TMD_IDW_Class:
	"""QGIS Plugin Implementation."""

	def __init__(self, iface):
		"""Constructor.

		:param iface: An interface instance that will be passed to this class
			which provides the hook by which you can manipulate the QGIS
			application at run time.
		:type iface: QgsInterface
		"""
		# Save reference to the QGIS interface
		self.iface = iface
		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'TMD_IDW_Class_{}.qm'.format(locale))

		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)
			QCoreApplication.installTranslator(self.translator)

		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&TMD_IDW')

		# Check if plugin was started the first time in current QGIS session
		# Must be set in initGui() to survive plugin reloads
		self.first_start = None

	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		"""Get the translation for a string using Qt translation API.

		We implement this ourselves since we do not inherit QObject.

		:param message: String for translation.
		:type message: str, QString

		:returns: Translated version of message.
		:rtype: QString
		"""
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('TMD_IDW_Class', message)


	def add_action(
		self,
		icon_path,
		text,
		callback,
		enabled_flag=True,
		add_to_menu=True,
		add_to_toolbar=True,
		status_tip=None,
		whats_this=None,
		parent=None):
		"""Add a toolbar icon to the toolbar.

		:param icon_path: Path to the icon for this action. Can be a resource
			path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
		:type icon_path: str

		:param text: Text that should be shown in menu items for this action.
		:type text: str

		:param callback: Function to be called when the action is triggered.
		:type callback: function

		:param enabled_flag: A flag indicating if the action should be enabled
			by default. Defaults to True.
		:type enabled_flag: bool

		:param add_to_menu: Flag indicating whether the action should also
			be added to the menu. Defaults to True.
		:type add_to_menu: bool

		:param add_to_toolbar: Flag indicating whether the action should also
			be added to the toolbar. Defaults to True.
		:type add_to_toolbar: bool

		:param status_tip: Optional text to show in a popup when mouse pointer
			hovers over the action.
		:type status_tip: str

		:param parent: Parent widget for the new action. Defaults None.
		:type parent: QWidget

		:param whats_this: Optional text to show in the status bar when the
			mouse pointer hovers over the action.

		:returns: The action that was created. Note that the action is also
			added to self.actions list.
		:rtype: QAction
		"""

		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)

		if status_tip is not None:
			action.setStatusTip(status_tip)

		if whats_this is not None:
			action.setWhatsThis(whats_this)

		if add_to_toolbar:
			# Adds plugin icon to Plugins toolbar
			self.iface.addToolBarIcon(action)

		if add_to_menu:
			self.iface.addPluginToMenu(
				self.menu,
				action)

		self.actions.append(action)

		return action

	def initGui(self):
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""

		icon_path = ':/plugins/tmd_idw/img/rain.png'
		self.add_action(
			icon_path,
			text=self.tr(u'TMD IDW'),
			callback=self.run,
			parent=self.iface.mainWindow())

		# will be set False in run()
		self.first_start = True


	def unload(self):
		"""Removes the plugin menu item and icon from QGIS GUI."""
		for action in self.actions:
			self.iface.removePluginMenu(
				self.tr(u'&TMD_IDW'),
				action)
			self.iface.removeToolBarIcon(action)



	def run(self):
		"""Run method that performs all the real work"""

		# Create the dialog with elements (after translation) and keep reference
		# Only create GUI ONCE in callback, so that it will only load when the plugin is started
		if self.first_start == True:
			self.first_start = False
			self.dlg = TMD_IDW_ClassDialog()
			self.dlg.run.clicked.connect(self.TMD_to_CSV)
			self.dlg.openBrowse.clicked.connect(self.OpenBrowse)
			self.append_layer_name()
			self.dlg.refresh.clicked.connect(self.append_layer_name)



		# show the dialog
		self.dlg.show()
		# Run the dialog event loop
		result = self.dlg.exec_()
		# See if OK was pressed
		if result:
			# Do something useful here - delete the line containing pass and
			# substitute with your code.
			pass


	def TMD_to_CSV(self):

		if self.dlg.output_path.text().strip() !="":

			self.check_type()
			if self.dlg.pixel_size.text().strip() !="":
				if self.check_type() == 'number':

					response =requests.get('http://data.tmd.go.th/api/WeatherToday/V1/?type=json')

					if response.status_code == 200:
						data=(response.json())
						#print(len(data['Stations']))
						if len(data['Stations']) > 0:
							#print("data")

							path_out=str(self.dlg.output_path.text()+'/Rain_IDW_'+date)
							#print(path_out+'.csv')

							output = path_out+'.csv'
							with open(output, 'w',encoding="utf-8") as file:
								file.write('Province,StationNameTh ,Latitude ,Longitude ,Date ,Rainfall\n')
								for line in data['Stations']:
									#print(line)
									try:
										file.write(str(line["StationNameEng"])+','+str(line["StationNameTh"])+','+str(line["Latitude"]["Value"])+','+str(line["Longitude"]["Value"])+','+str(line["Observe"]["Time"])+','+str(line["Observe"]["Rainfall"]["Value"])+','+str('\n'))
									except:
										pass

							file.close()

							url = "file:///"+output+"?encoding=%s&delimiter=%s&xField=%s&yField=%s&crs=%s" % ("UTF-8",",", "longitude", "latitude","epsg:4326")

							#Make a vector layer
							ly_csv=QgsVectorLayer(url,"CSV-data","delimitedtext")


							exp_crs = QgsCoordinateReferenceSystem(32647, QgsCoordinateReferenceSystem.EpsgCrsId)
							#ly_csv = QgsVectorLayer(layer.source(),layer.name(),'delimitedtext')
							writer = QgsVectorFileWriter.writeAsVectorFormat(ly_csv,path_out+'.shp','UTF-8',exp_crs,'ESRI Shapefile',False)


							ly_shp=QgsVectorLayer(path_out+'.shp',"IDW-data","ogr")
							QgsProject.instance().addMapLayer(ly_shp)

							self.IDW()


						else:
							QMessageBox.warning(self.dlg,u" DATA error "," No Stations data  ")
					#print(data)
					else:
						#print('requests Fail')
						QMessageBox.critical(self.dlg,u" API error "," requests Fail ")
				else:

					QMessageBox.information(self.dlg,u" Type error "," Pixcel size Fill in numbers only  ")

			else:
				QMessageBox.information(self.dlg,u"Error "," Fill Pixcel size Fill ")
				#print('pass')
		else:
			QMessageBox.information(self.dlg,u"Error directory"," Select output directory path ")
			#print('pass')

	def IDW(self):
		path_out=self.dlg.output_path.text()+'/Rain_IDW_'+date
		#print(pixel_size,'pixel_size')
		layer = self.iface.activeLayer()
		layer_data = QgsInterpolator.LayerData()
		layer_data.source = layer
		layer_data.zCoordInterpolation = False
		layer_data.interpolationAttribute = 5
		layer_data.sourceType = QgsInterpolator.SourcePoints
		tin_interpolator = QgsIDWInterpolator([layer_data])
		tin_interpolator.setDistanceCoefficient(2)

		export_path = path_out+".tiff"


		if self.dlg.exten.currentText() != 'default':

			vl = QgsProject.instance().mapLayersByName(self.dlg.exten.currentText())[0]
			self.iface.setActiveLayer(vl)
			layer = self.iface.activeLayer()

			#extent
			rect = layer.extent()
			res = pixel_size
			ncol = int( ( rect.xMaximum() - rect.xMinimum() ) / res )
			nrows = int( (rect.yMaximum() - rect.yMinimum() ) / res)

		else:
			rect = layer.extent()
			res = pixel_size
			ncol = int( ( rect.xMaximum() - rect.xMinimum() ) / res )
			nrows = int( (rect.yMaximum() - rect.yMinimum() ) / res)

		output = QgsGridFileWriter(tin_interpolator,export_path,rect,ncol,nrows)
		output.writeFile()


		#extent
		rlayer = self.iface.addRasterLayer(export_path, "interpolation_output")
		self.dlg.output_path.clear()
		self.dlg.pixel_size.clear()



	def OpenBrowse(self):
		filename1 = QFileDialog.getExistingDirectory(self.dlg, "Select output directory path ",)

		self.dlg.output_path.setText(filename1)

	def append_layer_name(self):
		self.dlg.exten.clear()
		layer_name1=['default']
		layer_all=QgsProject.instance().mapLayers().values()
		for i in layer_all :
			layer_name1.append(i.name())
		#print(layer_name1)

		self.dlg.exten.addItems(layer_name1)

	def check_type (self):
		global pixel_size

		number = self.dlg.pixel_size.text()
		try:
			#number = int(number)
			pixel_size=int(number)

			return('number')
		except Exception:
			return('not number')
			#pass









