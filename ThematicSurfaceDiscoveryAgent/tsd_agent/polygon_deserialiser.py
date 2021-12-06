__all__ = ['deserialise_polygon_2d', 'deserialise_polygon_3d']


def deserialise_polygon_2d(geometry_string, datatype, transformer=None, flip_xy_out=False):
    '''
    Returns jagged array of rings' xy coordinates, as well as a flat array of z coordinates.
    The jagged array is a list of rings, each of which is a list of coordinates, each of which
    is a tuple of x and y. The first ring is the exterior ring and all remaining are interior.
    '''
    flat_coords = [float(number) for number in geometry_string.split('#')]
    xy = [(float(flat_coords[i*3]), float(flat_coords[i*3+1]))
          for i in range(len(flat_coords)//3)]
    if transformer != None:
        for i in range(len(xy)):
            x, y = transformer.transform(xy[i][0], xy[i][1])
            xy[i] = (y, x) if flip_xy_out else (x, y)
    z = [float(flat_coords[i*3+2]) for i in range(len(flat_coords)//3)]
    ring_sizes = datatype.split('-')
    ring_sizes = ring_sizes[(ring_sizes.index('3')+1):]
    coords = []
    for ring_size in ring_sizes:
        coords.append(xy[:int(ring_size)//3])
        xy = xy[int(ring_size)//3:]
    return coords, z


def deserialise_polygon_3d(geometry_string, datatype, transformer=None, flip_xy_out=False):
    '''
    Returns a jagged array of rings' xyz coordinates. The jagged array is a list of rings, each
    of which is a list of coordinates, each of which is a tuple of x, y, z.
    '''
    flat_coords = [float(number) for number in geometry_string.split('#')]
    xyz = [(float(flat_coords[i*3]), float(flat_coords[i*3+1]), float(flat_coords[i*3+2]))
           for i in range(len(flat_coords)//3)]
    if transformer != None:
        for i in range(len(xyz)):
            x, y, z = transformer.transform(xyz[i][0], xyz[i][1], xyz[i][2])
            xyz[i] = (y, x, z) if flip_xy_out else (x, y, z)
    ring_sizes = datatype.split('-')
    ring_sizes = ring_sizes[(ring_sizes.index('3')+1):]
    coords = []
    for ring_size in ring_sizes:
        coords.append(xyz[:int(ring_size)//3])
        xyz = xyz[int(ring_size)//3:]
    return coords
