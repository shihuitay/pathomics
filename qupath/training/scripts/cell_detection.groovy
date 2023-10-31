import qupath.lib.gui.scripting.QPEx
import javax.swing.JFileChooser
import java.io.FileWriter
import java.io.IOException

// Select all annotations
def annotations = getAnnotationObjects()
selectObjects(annotations)

runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', '{"detectionImageBrightfield":"Optical density sum","requestedPixelSizeMicrons":0.2,"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":1.5,"minAreaMicrons":1.0,"maxAreaMicrons":400.0,"threshold":0.1,"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":5.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}')