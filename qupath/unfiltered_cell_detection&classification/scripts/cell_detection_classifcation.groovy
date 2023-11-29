/**
 * Script to perform cell detection, classification & counting on the WSI
 * export the results (cell counts for each category as csv file)
 */

import qupath.lib.gui.scripting.QPEx
import javax.swing.JFileChooser
import java.io.FileWriter
import java.io.IOException

parent_dir = '/Users/shihuitay/Desktop/pathomics/data/250/'
def name = getCurrentServer().getMetadata().getName()
def filename = name.split("\\.")[0]
println "${filename}"
setImageType('BRIGHTFIELD_H_E');
setColorDeconvolutionStains('{"Name" : "H&E estimated", "Stain 1" : "Hematoxylin", "Values 1" : "0.62812 0.71231 0.31318", "Stain 2" : "Eosin", "Values 2" : "0.23757 0.93412 0.26644", "Background" : " 221 217 228"}');

// Select all annotations
def annotations = getAnnotationObjects()
selectObjects(annotations)

// run cell detection and classification
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', '{"detectionImageBrightfield":"Optical density sum","requestedPixelSizeMicrons":0.2,"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":1.5,"minAreaMicrons":1.0,"maxAreaMicrons":400.0,"threshold":0.1,"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":5.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}')
runObjectClassifier("tumor_immune_021123")

def detection = getDetectionObjects()
def detectionCounts = detection.size()
def annotationTumorCounts = [:]
def annotationImmuneCounts = [:]

// Calculate tumor cell counts for each annotation
annotations.each { annotation ->
    def tumorCountObjects = annotation.getChildObjects().findAll { obj ->
        obj.getPathClass()== getPathClass("Tumor")
    }
    annotationTumorCounts[annotation] = tumorCountObjects.size()
}

// Calculate immune cell counts for each annotation
annotations.each { annotation ->
    def immuneCountObjects = annotation.getChildObjects().findAll { obj ->
        obj.getPathClass()== getPathClass("Immune cells") 
    }
    annotationImmuneCounts[annotation] = immuneCountObjects.size()
}

// Get the key index
def tumorAnnotations = annotationTumorCounts.collect { it.key }

// Create CSV content
def csvCells = "Filename, Number of Tumor Cell,Number of Immune Cell,Number of Detection\n" +
                 tumorAnnotations.collect { annotation ->
                     "${filename},${annotationTumorCounts[annotation]}, ${annotationImmuneCounts[annotation]}, ${detectionCounts}"
                 }.join('\n')


// Write CSV content to the file
try {
    def csvWriter = new FileWriter("${parent_dir}/${filename}/WSI_detection.csv")
    csvWriter.append(csvCells.toString())
    csvWriter.flush()
    csvWriter.close()
    println("CSV file saved successfully.")
} catch (IOException e) {
    e.printStackTrace()
    println("Failed to save CSV file.")
}
