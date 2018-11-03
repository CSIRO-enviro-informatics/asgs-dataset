function meters2degress(x, y) {
    var lon = x * 180.0 / 20037508.34;
    var lat = Math.atan(Math.exp(y * Math.PI / 20037508.34)) * 360.0 / Math.PI - 90.0;
    return [lon, lat]
}

function geom_convert(geom, dims) {
    if (!geom.hasOwnProperty('type')) {
        return []
    }
    if (!dims) {
        dims = 2;
    }

    var convert_poly_part = function (poly_part) {
        var new_poly_part = [];
        for (var i = 0, l = poly_part.length; i < l; i++) {
            var poly_part_segment = poly_part[i];
            if (poly_part_segment.length < dims) {
                // Wrong number of dims!
                return new_poly_part;
            }
            var lonlat = meters2degress(poly_part_segment[0], poly_part_segment[1]);
            if (dims > 2) {
                lonlat[2] = poly_part_segment[2];
            }
            if (dims > 3) {
                lonlat[3] = poly_part_segment[3];
            }
            new_poly_part.push(lonlat);
        }
        return new_poly_part;
    };

    var convert_poly = function (poly) {
        var new_poly_parts = [];
        for (var i = 0, l = poly.length; i < l; i++) {
            var poly_part = poly[i];
            new_poly_parts.push(convert_poly_part(poly_part));
        }
        return new_poly_parts;
    };


    var type = geom.type;
    var coords = geom.coordinates;
    if (geom.hasOwnProperty('dims')) {
        dims = parseInt(geom.dims);
    }
    if (type === "MultiPolygon") {
        geom.coordinates = [];
        for (var i = 0, l = coords.length; i < l; i++) {
            var c = coords[i];
            geom.coordinates.push(convert_poly(c));
        }
    } else if (type === "Polygon") {
        geom.coordinates = convert_poly(coords);
    } else {
        console.error("Unknown Geojson format: " + type);
    }
    return geom;
}
