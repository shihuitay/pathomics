/**
 * Script to import annotations, cell detection, classification & counting
 * export the results (cell counts for each category as csv file)
 */

import qupath.lib.gui.scripting.QPEx
import javax.swing.JFileChooser
import java.io.FileWriter
import java.io.IOException

/// import annotation
parent_dir = '/Users/shihuitay/Desktop/pathomics/data/250/'
def name = getCurrentServer().getMetadata().getName()
def filename = name.split("\\.")[0]
println "${filename}"
def gson = GsonTools.getInstance(true)
def json = new File("${parent_dir}${filename}/${filename}.geojson").text

//// Read the annotations
def type = new com.google.gson.reflect.TypeToken<List<qupath.lib.objects.PathObject>>() {}.getType()
def deserializedAnnotations = gson.fromJson(json, type)

//// Set the annotations to have a different name (so we can identify them) & add to the current image
addObjects(deserializedAnnotations)     

setImageType('BRIGHTFIELD_H_E');
setColorDeconvolutionStains('{"Name" : "H&E estimated", "Stain 1" : "Hematoxylin", "Values 1" : "0.62812 0.71231 0.31318", "Stain 2" : "Eosin", "Values 2" : "0.23757 0.93412 0.26644", "Background" : " 221 217 228"}');

// Select all annotations
def annotations = getAnnotationObjects()
def totalAnnotationCount = annotations.size()
selectObjects(annotations)

// run cell detection and classification
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', '{"detectionImageBrightfield":"Optical density sum","requestedPixelSizeMicrons":0.2,"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":1.5,"minAreaMicrons":1.0,"maxAreaMicrons":400.0,"threshold":0.1,"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":5.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}')
runObjectClassifier("tumor vs immune 6") 

def annotationTumorCounts = [:]
def annotationImmuneCounts = [:]

// Calculate tumor cell counts for each annotation
annotations.each { annotation ->
    def tumorCountObjects = annotation.getChildObjects().findAll { obj ->
        obj.getPathClass()== getPathClass("Tumor") // Replace with the appropriate method
    }
    annotationTumorCounts[annotation] = tumorCountObjects.size()
}

// Calculate immune cell counts for each annotation
annotations.each { annotation ->
    def immuneCountObjects = annotation.getChildObjects().findAll { obj ->
        obj.getPathClass()== getPathClass("Immune cells") // Replace with the appropriate method
    }
    annotationImmuneCounts[annotation] = immuneCountObjects.size()
}

// Get the key index
def tumorAnnotations = annotationTumorCounts.collect { it.key }

// Create CSV content
def csvCells = "Object ID,Number of Tumor Cell,Number of Immune Cell\n" +
                 tumorAnnotations.collect { annotation ->
                     "${annotation.getID()},${annotationTumorCounts[annotation]}, ${annotationImmuneCounts[annotation]}"
                 }.join('\n')
            

// Write CSV content to the file
try {
    def csvWriter = new FileWriter("${parent_dir}/${filename}/detection.csv")
    csvWriter.append(csvCells.toString())
    csvWriter.flush()
    csvWriter.close()
    println("CSV file saved successfully.")
} catch (IOException e) {
    e.printStackTrace()
    println("Failed to save CSV file.")
}

