// KSA NFI LULC validation: Earth Engine sampling at office plot points
// Operational run used the Earth Engine Python API with the same collections,
// dates, mask, reducer and scale. This is the equivalent Code Editor script.
//
// Inputs
//   plots: ee.FeatureCollection of office/database coordinates (EPSG:4326)
//          properties: plot_uid, su_no, plot_no
// Outputs
//   esa_code: ESA WorldCover v200 Map class at 10 m
//   dry_ndvi_median: August 2024 Sentinel-2 L2A cloud-masked median NDVI

var esa = ee.ImageCollection('ESA/WorldCover/v200')
  .first()
  .select('Map')
  .rename('esa_code');

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterDate('2024-08-01', '2024-09-01')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60));

var cp = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
  .filterDate('2024-08-01', '2024-09-01');

var joinedS2 = ee.ImageCollection(
  ee.Join.saveFirst('cloud_prob').apply({
    primary: s2,
    secondary: cp,
    condition: ee.Filter.equals({
      leftField: 'system:index',
      rightField: 'system:index'
    })
  })
);

function prepDryNdvi(img) {
  var cloud = ee.Image(img.get('cloud_prob')).select('probability');
  var scl = img.select('SCL');
  var mask = cloud.lt(40)
    .and(scl.neq(3))
    .and(scl.neq(8))
    .and(scl.neq(9))
    .and(scl.neq(10))
    .and(scl.neq(11));
  var ndvi = img.normalizedDifference(['B8', 'B4']).rename('dry_ndvi_median');
  return ndvi.updateMask(mask);
}

var dryNdvi = joinedS2.map(prepDryNdvi)
  .median()
  .rename('dry_ndvi_median')
  .set({
    product: 'Saudi_2024_Dry_NDVI_Median',
    period: '2024-08',
    note: 'Point-sampled equivalent of cancelled national mosaic export'
  });

var stack = esa.addBands(dryNdvi);

// plots must already exist as a FeatureCollection of office lon/lat points.
var sampled = stack.reduceRegions({
  collection: plots,
  reducer: ee.Reducer.first(),
  scale: 10,
  tileScale: 4
});

Map.addLayer(esa, {min: 10, max: 100}, 'ESA WorldCover v200');
Map.addLayer(dryNdvi, {min: 0, max: 0.6, palette: ['#f7f1e1', '#2a9d8f']}, 'Dry NDVI Aug 2024');
Map.addLayer(plots, {color: 'red'}, 'Office plot points');
print('Sampled features', sampled.limit(20));
