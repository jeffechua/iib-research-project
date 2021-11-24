<?xml version="1.0" encoding="UTF-8"?>
<core:CityModel xmlns:brid="http://www.opengis.net/citygml/bridge/2.0" xmlns:tran="http://www.opengis.net/citygml/transportation/2.0" xmlns:frn="http://www.opengis.net/citygml/cityfurniture/2.0" xmlns:wtr="http://www.opengis.net/citygml/waterbody/2.0" xmlns:sch="http://www.ascc.net/xml/schematron" xmlns:veg="http://www.opengis.net/citygml/vegetation/2.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:tun="http://www.opengis.net/citygml/tunnel/2.0" xmlns:tex="http://www.opengis.net/citygml/texturedsurface/2.0" xmlns:gml="http://www.opengis.net/gml" xmlns:gen="http://www.opengis.net/citygml/generics/2.0" xmlns:dem="http://www.opengis.net/citygml/relief/2.0" xmlns:app="http://www.opengis.net/citygml/appearance/2.0" xmlns:luse="http://www.opengis.net/citygml/landuse/2.0" xmlns:xAL="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0" xmlns:bldg="http://www.opengis.net/citygml/building/2.0" xmlns:smil20="http://www.w3.org/2001/SMIL20/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:smil20lang="http://www.w3.org/2001/SMIL20/Language" xmlns:pbase="http://www.opengis.net/citygml/profiles/base/2.0" xmlns:core="http://www.opengis.net/citygml/2.0" xmlns:grp="http://www.opengis.net/citygml/cityobjectgroup/2.0">
    <gml:boundedBy>
        <gml:Envelope srsName="EPSG:27700" srsDimension="3">
            <gml:lowerCorner>543352.4499999599 259131.94999899538 12.23</gml:lowerCorner>
            <gml:upperCorner>543895.9500000007 259593.54999944256 36.15</gml:upperCorner>
        </gml:Envelope>
    </gml:boundedBy>
    <core:cityObjectMember>
        <bldg:Building gml:id="testbuilding">
            <bldg:lod1MultiSurface>
                <gml:MultiSurface srsName="EPSG:27700" srsDimension="3">
                    <gml:surfaceMember>
                        <gml:CompositeSurface>
                            <gml:surfaceMember>
                                <gml:Polygon>
                                    <gml:exterior>
                                        <gml:LinearRing>
                                            <gml:posList>0 0 0 3 0 0 3 3 0 0 3 0 0 0 0</gml:posList>
                                        </gml:LinearRing>
                                    </gml:exterior>
                                    <gml:interior>
                                        <gml:LinearRing>
                                            <gml:posList>1 1 0 1 2 0 2 2 0 2 1 0 1 1 0</gml:posList>
                                        </gml:LinearRing>
                                    </gml:interior>
                                </gml:Polygon>
                            </gml:surfaceMember>
                        </gml:CompositeSurface>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod1MultiSurface>
        </bldg:Building>
    </core:cityObjectMember>
</core:CityModel>