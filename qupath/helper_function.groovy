/***** export cell measurements *****/
selectCells();
exportSelectedObjectsToGeoJson(filename_string, “FEATURE_COLLECTION”)


/***** export annotations *****/
Set annotationMeasurements = []
getAnnotationObjects().each{
it.getMeasurementList().getMeasurementNames().each{
annotationMeasurements << it}}
annotationMeasurements.each{ removeMeasurements(QuPath.lib.objects.PathCellObject, it);}
boolean prettyPrint = false
// false results in smaller file sizes and thus faster loading times, at the cost of nice formating
def gson = GsonTools.getInstance(prettyPrint)
def annotations = getAnnotationObjects()
File file = new File('/Users/shihuitay/test.json')
 file.withWriter('UTF-8') {
     gson.toJson(annotations,it)
 }


 /***** stardist *****/
 import qupath.ext.stardist.StarDist2D
// Specify the model file
var pathModel = '/Users/shihuitay/QuPath/he_heavy_augment.pb'
var stardist = StarDist2D.builder(pathModel)
      .threshold(0.5)              // Prediction threshold
      .normalizePercentiles(1, 99) // Percentile normalization
      .pixelSize(0.5)              // Resolution for detection
      .build()
// Run detection for the selected objects
var imageData = getCurrentImageData()
var pathObjects = getSelectedObjects()
if (pathObjects.isEmpty()) {
    Dialogs.showErrorMessage("StarDist", "Please select a parent object!")
    return
}
stardist.detectObjects(imageData, pathObjects)
println 'Done!'


/***** import geojson for all images *****/
def name = getCurrentServer().getMetadata().getName()
def filename = name.split("\\.")[0]
println "${filename}"
def gson = GsonTools.getInstance(true)
def json = new File("/Users/shihuitay/Desktop/pathomics/data/250/${filename}/${filename}.geojson").text
//// Read the annotations
def type = new com.google.gson.reflect.TypeToken<List<qupath.lib.objects.PathObject>>() {}.getType()
def deserializedAnnotations = gson.fromJson(json, type)
//// Set the annotations to have a different name (so we can identify them) & add to the current image
addObjects(deserializedAnnotations)   


/***** delete all annotations *****/
def annotations = getAnnotationObjects() // Get a list of all annotation objects
removeObjects(annotations, false)  // true means keep the descendents
println("All annotations have been deleted.")


/***** crop/save the region of the currently selected object *****/
def server = getCurrentServer()
def name = getCurrentServer().getMetadata().getName()
def annotations = getAnnotationObjects()
annotations.each { annotation ->
    def roi = annotation.getROI()
    def requestROI = RegionRequest.createInstance(server.getPath(), 2, roi)
    writeImageRegion(server, requestROI, "/Users/shihuitay/Desktop/pathomics/data/cropped/${name}")
    print "Done! ${name}"}
// Write the region of the image corresponding to the currently-selected object
def server = getCurrentServer()
def name = getCurrentServer().getMetadata().getName()
def annotations = getAnnotationObjects()
//def outputFileName = name.tokenize('.')[0] + '.ome.tif'
//print outputFileName
annotations.each { annotation ->
    def roi = annotation.getROI()
    def requestROI = RegionRequest.createInstance(server.getPath(), 1, roi)
    writeImageRegion(server, requestROI, "/Users/shihuitay/Desktop/pathomics/data/cropped/${name}")
    print "Done! ${name}"}