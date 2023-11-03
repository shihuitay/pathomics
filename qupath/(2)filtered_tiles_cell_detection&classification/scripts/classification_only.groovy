/**
 * Script to import annotations and perform cell detection, classification & counting on annotated (selected) tiles
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

// Select all annotations
def annotations = getAnnotationObjects()
selectObjects(annotations)

// reset classification

// run cell classification
runObjectClassifier("tumor_immune_021123") 

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

