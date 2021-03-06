# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Soil
                                 A QGIS plugin
 el plugin genera sitios de muestreo para suelos degradados por salinización
                              -------------------
        begin                : 2017-09-30
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Lina Viasús - Gerardo Chaparro
        email                : lviasus1@gmail.com - ingerardoch@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import iface
from qgis.analysis import QgsGeometryAnalyzer
from PyQt4 import QtCore, QtGui
from osgeo import ogr
from qgis.gui import QgsMessageBar
import processing
import random
import sys
sys.path.append('C:\Users\toshiba\.qgis2\python\plugins')
import processing

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from soil_logyc_dialog import SoilDialog
import os.path




class Soil:
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
        #pluginPath = QFileInfo(os.path.realpath(__file__)).path()
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Soil_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QS4')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Soil')
        self.toolbar.setObjectName(u'Soil')

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
        return QCoreApplication.translate('Soil', message)


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

        # Create the dialog (after translation) and keep reference
        self.dlg = SoilDialog()
        self.dlg.gen_muestreo.clicked.connect(self.gen_muestreo)
        # Boton Guardar
        #self.dlg.guardar.clicked.connect(self.guardar_clicked)

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Soil/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'QS4'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QS4'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        self.dlg.comboBox.clear()
        self.dlg.capavias.clear()
        self.dlg.capacurvas.clear()
        self.dlg.capasuelos.clear()
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                layer_list.append(layer.name())
            else:
                layer_list.append(layer.name())

        self.dlg.comboBox.addItems(layer_list)
        self.dlg.capacurvas.addItems(layer_list)
        self.dlg.capavias.addItems(layer_list)
        self.dlg.capasuelos.addItems(layer_list)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


    def gen_muestreo(self):

		#Se leen los vectores que esten el la lista de capas cargada en QGis
        layers = self.iface.legendInterface().layers()

		#Selecciona la capa de universo muestreal (área de estudio)
        selectedLayerIndex = self.dlg.comboBox.currentIndex()
        selectedLayer = layers[selectedLayerIndex]
        area_est = selectedLayer

        #inicio de la edición
        selectedLayer.startEditing()

        #agregar nuevo campo
        selectedLayer.dataProvider().addAttributes([QgsField("Area_Ha", QVariant.Int)])

        #Cierra edicion
        selectedLayer.commitChanges()

        #Activa edicion
        selectedLayer.startEditing()
        idx = selectedLayer.fieldNameIndex( "Area_Ha" )

        #Calculo de área en Ha mediante expresion
        e = QgsExpression( "$area/10000" )
        e.prepare(selectedLayer.pendingFields())
        for f in selectedLayer.getFeatures():
                value = e.evaluate (f)
                selectedLayer.changeAttributeValue (f.id(), idx, value)

        area_est.deselect(0)
        #atualizción de columna
        #cierre de edición
        selectedLayer.updateFields()
        selectedLayer.commitChanges()


        # definición de variables para estimar tamaño de muestra
        marg_error = self.dlg.marg_error.value()
        nivel_conf = self.dlg.nivel_conf.value()
        universo = int(value)

        #selección del tamaño de muestra

        if universo < 100000:
            muestra = (universo * (nivel_conf*nivel_conf * 0.5 * 0.5)) / ((universo - 1) * (marg_error*marg_error) + (nivel_conf * 0.5* 0.5))
            QMessageBox.information(self.dlg,"POBLACION FINITA", "Tamano de muestra: " + str(int(muestra)))

        else:
            muestra = ((nivel_conf**2) * 0.5 * 0.5) / (marg_error**2)
            QMessageBox.information(self.dlg,"POBLACION INFINITA", "Tamano de muestra: " + str(int(muestra)))

        #Se parsea a entero el tamaño de muestra
        muestra_int = int(muestra)

        #Generación de los buffer sobre la capa vías
        # Se leen los vectores que esten el la lista de capas cargada en QGis
        layers = self.iface.legendInterface().layers()

        # Selecciona la capa vial para hacer multibuffer (capa de vías)
        selectedLayerIndex = self.dlg.capavias.currentIndex()
        selectedLayer = layers[selectedLayerIndex]

        # Generar el buffer de la capa vias
        vias = selectedLayer
        QgsGeometryAnalyzer().buffer(vias, "C:/Users/toshiba/Downloads/buffer_vias100.shp", 100, False, True, -1)
        QgsGeometryAnalyzer().buffer(vias, "C:/Users/toshiba/Downloads/buffer_vias200.shp", 200, False, True, -1)
        QgsGeometryAnalyzer().buffer(vias, "C:/Users/toshiba/Downloads/buffer_vias300.shp", 300, False, True, -1)
        QgsGeometryAnalyzer().buffer(vias, "C:/Users/toshiba/Downloads/buffer_vias400.shp", 400, False, True, -1)
        QgsGeometryAnalyzer().buffer(vias, "C:/Users/toshiba/Downloads/buffer_vias500.shp", 500, False, True, -1)
        buffer_vias500 = iface.addVectorLayer("C:/Users/toshiba/Downloads/buffer_vias500.shp", "", "ogr")
        buffer_vias400 = iface.addVectorLayer("C:/Users/toshiba/Downloads/buffer_vias400.shp", "", "ogr")
        buffer_vias300 = iface.addVectorLayer("C:/Users/toshiba/Downloads/buffer_vias300.shp", "", "ogr")
        buffer_vias200 = iface.addVectorLayer("C:/Users/toshiba/Downloads/buffer_vias200.shp", "", "ogr")
        buffer_vias100 = iface.addVectorLayer("C:/Users/toshiba/Downloads/buffer_vias100.shp", "", "ogr")


        #Generación de puntos de muestreo
        processing.runalg('qgis:randompointsinsidepolygonsfixed', vias, 0, muestra_int, 0, "C:/Users/toshiba/Downloads/sitios_muestreo.shp")
        sitios_muestreo = iface.addVectorLayer("C:/Users/toshiba/Downloads/sitios_muestreo.shp", "", "ogr")
        QMessageBox.information(self.dlg, "MENSAJE", "Typo de dato: " + str(type(sitios_muestreo)))


        """""
        registry = QgsMapLayerRegistry.instance()
        QgsMapLayerRegistry.addMapLayer(QgsMapLayer, True)
        return layer




        # select feature
        feat = vias.select(0)



        # get geometry
        geom = feat.geometry()

        # determine buffer 500 m
        buffer = geom.buffer(500, -1)

        # Extract CRS from route
        CRS = vias.crs().postgisSrid()

        URI = "Polygon?crs=epsg:" + str(CRS) + "&field=id:integer""&index=yes"

        # Create polygon layer for buffer
        mem_layer = QgsVectorLayer(URI,
                                   "buffer",
                                   "memory")

        # add Map Layer to Registry
        QgsMapLayerRegistry.instance().addMapLayer(mem_layer)

        # Prepare mem_layer for editing
        mem_layer.startEditing()

        # Set feature for buffer
        feat2 = QgsFeature()

        # Set geometry for buffer
        feat2.setGeometry(buffer)

        # set attributes values for buffer
        feat2.setAttributes([1])

        mem_layer.addFeature(feat2, True)

        # stop editing and save changes
        mem_layer.commitChanges()

        # deselect feature
        vias.deselect(0)

        # zoom to Active Layer (now is buffer)
        iface.zoomToActiveLayer()



  		#Generar el buffer de la capa vias



        feat_p9 = buffer_vias500.getFeatures().next()
        feat_p10 = buffer_vias400.getFeatures().next()

        diff1 = feat_p9.geometry().difference(feat_p10.geometry())
        QMessageBox.information(self.dlg,"MENSAJE", "Tipo de dato: " + str(type(diff1)))
        #print [diff1]
        #diff11 = QgsVectorLayer(diff1,"anillo100", "",  "")

        #generación de puntos aleatorios
        def createQgsPoints(coor):
            return [QgsPoint(coor[i], coor[i + 1]) for i in range(0, len(coor), 2)]

        def createPointRandomLayer(num_points):
            layer = iface.activeLayer()



            crs = layer.crs()
            epsg = crs.postgisSrid()

            extent = layer.extent()

            xmax = extent.xMaximum()
            xmin = extent.xMinimum()
            ymax = extent.yMaximum()
            ymin = extent.yMinimum()

            coor = []

            for i in range(num_points):
                xRandom = random.uniform(xmin, xmax)
                yRandom = random.uniform(ymin, ymax)
                coor.append(xRandom)
                coor.append(yRandom)

            CRS = QgsCoordinateReferenceSystem(epsg)

            uri = "Point?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes"

            mem_layer = QgsVectorLayer(uri,"Sitios de muestreo","memory")

            # add Map Layer to Registry
            QgsMapLayerRegistry.instance().addMapLayer(mem_layer)

            # Prepare mem_layer for editing
            mem_layer.startEditing()

            # points to add
            points = createQgsPoints(coor)
            # Calculate number points
            n = len(points)

            # Set feature
            feature = []

            for i in range(n):
                feat = QgsFeature()
                feature.append(feat)

            # set attributes values
            for i in range(n):
                feature[i].setGeometry(QgsGeometry.fromPoint(points[i]))  # Set geometry
                feature[i].setAttributes([i])
                mem_layer.addFeature(feature[i], True)

            # stop editing and save changes
            mem_layer.commitChanges()
        # Creación de puntos igual al tamaño de muestra
        createPointRandomLayer(muestra_int)












                QMessageBox.information(self.dlg,"MENSAJE", "Tipo de dato: " + str(type(vias)))
        geometry = QgsVectorLayer().getGeometry()
        geom = geometry(vias)
        buffer = vias.buffer(100,-1)
        CRS = vias.crs().postgisSrid()
        URI = "Polygon?crs=epsg:"+str(CRS)+"&field=id:integer""&index=yes"
        mem_layer = QgsVectorLayer(URI, "buffer_100", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
        mem_layer.startEditing()
        feat2 = QgsFeature()
        feat2.setGeometry(buffer)
        feat2.setAttributes([1])
        mem_layer.addFeature(feat2, True)
        mem_layer.commitChanges()




        layer =  QgsVectorLayer('Polygon', 'poly' , "memory")
        pr = layer.dataProvider()
        poly = QgsFeature()
        #points = [point1,QgsPoint(50,150),point2,QgsPoint(100,50)]
        # or points = [QgsPoint(50,50),QgsPoint(50,150),QgsPoint(100,150),QgsPoint(100,50)]
        poly.setGeometry(QgsGeometry.fromPolygon([diff1]))
        pr.addFeatures([poly])
        layer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayers([layer])


        #processing.runandload("qgis:polygonintersections",buffer_vias200, buffer_vias100, "", "", "C:/Users/toshiba/Downloads"  )
        #processing.runalg('', diferencia, diferencia.shp)
        #diferencia = QgsVectorLayer("C:/Users/toshiba/Downloads ", "diferencia", "ogr" )



        crs = QgsCoordinateReferenceSystem(crs, QgsCoordinateReferenceSystem.PostgisCrsId)
        typeString = "%s?crs=%s" % (typeString, crs.authid())
        layer = QgsVectorLayer(typeString, diff1, "memory")
        layer.dataProvider().addAttributes([QgsField("name", QVariant.String)])
        registry = QgsMapLayerRegistry.instance()
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        return layer





        #QgsMapLayerRegistry.instance().addMapLayer(diff1, True)

        #iface.addVectorLayer(diff1, "diff1", "ogr")
        #diff2 = feat_p10.geometry().difference(feat_p9.geometry()).exportToWkt()
        #print diff1




        #Interseccion de gemotrías
        line = buffer_vias500
        grid = buffer_vias400

        for i in grid.getFeatures():
            for l in line.getFeatures():
                if i.geometry().intersects(l.geometry()):
                # add the selection to the layer
                    grid.select(i.id())

        #seleccionar DEM
		#Se leen los vectores que esten el la lista de capas cargada en QGis
        layers = self.iface.legendInterface().layers()

		#Selecciona la capa vial para hacer multibuffer (capa de vías)
        selectedLayerIndex = self.dlg.capacurvas.currentIndex()
        selectedLayer = layers[selectedLayerIndex]
        dem = selectedLayer
        #QgsRasterLayer().slopeAtPercent()






    def guardar_clicked(self):
        self.guardar = QtGui.QFileDialog.getSaveFileName(self.dlg, 'Guardar Archivo',".", "ShapeFile (*.shp)")
        self.dlg.save.setText(self.guardar)

          # display file dialog for output shapefile
        self.outShape.clear()
        fileDialog = QFileDialog()
        fileDialog.setConfirmOverwrite(False)
        outName = fileDialog.getSaveFileName(self, "Output Shapefile",".", "Shapefiles (*.shp)")
        outPath = QFileInfo(outName).absoluteFilePath()
        if not outPath.upper().endswith(".SHP"):
           outPath = outPath + ".shp"
        if outName:
            self.outShape.clear()
        self.outShape.insert(outPath)

"""






