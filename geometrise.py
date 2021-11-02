import warnings
warnings.filterwarnings(
    'ignore', message='.* is incompatible with the GEOS version PyGEOS was compiled with .*')

import numpy as np
import earcut
import geopandas
import os
from helpers import *

__all__ = ['vertices', 'triangles', 'o', 'data']

timer = Timer()

# find all gdb files
paths = []
for path, dirs, files in os.walk('download/heights/tl/'):
    for dir in dirs:
        if dir.endswith('.gdb'):
            paths.append(os.path.join(path, dir))
paths = paths[1:3]
# load them
columns = ['abshmin', 'absh2', 'geometry']
write(f'Loading gdb files... (1/{len(paths)})')
data = geopandas.read_file(paths.pop())[columns]
for i in range(len(paths)):
    write(f'Loading gdb files... ({i+2}/{len(paths)+1})')
    data = data.append(geopandas.read_file(paths[i])[columns],
                       ignore_index=True)
print(f' done. ({timer.lap(2)}s)')

write(f'Exploding multipolygons... {len(data.index)}->')
data = data.explode('geometry', index_parts=False)
print(f'{len(data.index)}. ({timer.lap(2)}s)')

# Fetch a random location as origin for reference. Note that the geometries are multipolygons,
# but of size 1, so they are essentially just polygons (and in Topography Layer, they are)
o = data.geometry[0].exterior.centroid

# build model
all_vs = []     # serialised vector6 array
all_trigs = []  # serialised int-triple array
reporter = Timer(0)
t1 = Timer()
t2 = Timer()
t3 = Timer()
# it's stupid but this is inexplicably the fastest method?
# see https://towardsdatascience.com/4dad88ac92ee
# I verified against [for i in data.index] and data.geometry[i]
write(f'Vectorising for processing...')
# suspect geopandas is converting to PyGEOS polygons here because this only started being slow after I imported PyGEOS
data_dict = data.to_dict('records')
print(f' done. ({timer.lap(2)}s)')
for i, row in enumerate(data_dict):
    t1.start()
    geometry = row['geometry']
    bottom = row['abshmin']
    top = row['absh2']
    # report on progress; due to the number of buildings, only do this at 2 Hz
    if reporter.current() > 0.5:
        reporter.lap()
        write(f'Triangulating buildings ({i}/{len(data.index)})...')
    # serialise polygon data for further processing
    poly_vs = []  # serialised vector2 array
    for point in geometry.exterior.coords:
        poly_vs.extend(point)
    holes = []    # indices where holes start
    for hole in geometry.interiors:
        holes.append(len(poly_vs)//2)
        for point in hole.coords:
            poly_vs.extend(point)
    t1.stop()
    # earcut (constrained triangulation of polygon with holes)
    t2.start()
    triangle_sublist = earcut.earcut(poly_vs, holes)
    t2.stop()
    # construct the actual model vertices and triangles
    t3.start()
    # next vertex index in all_vs i.e. index of first vertex from this poly
    offset = len(all_vs)//6
    all_trigs.extend([offset+j*2 for j in triangle_sublist])
    for j in range(len(poly_vs)//2):
        # j is the vertex index in the poly_vs array (earcut vec2 points), which corresponds to
        # offset+j*2 (top), offset+j*2+1 (bottom) vertex indices in the all_vs array (model vec6 points).
        # So the actual all_vs elements corresponding to j are:
        #  (offset+j*2)*6   = top vertex x coord  (x)      (offset+j*2+1)*6   = bottom vertex x coord (x)
        #  (offset+j*2)*6+1 = top vertex y coord  (top)    (offset+j*2+1)*6+1 = bottom vertex y coord (bottom)
        #  (offset+j*2)*6+2 = top vertex z coord  (y)      (offset+j*2+1)*6+2 = bottom vertex z coord (y)
        #  (offset+j*2)*6+3 = top vertex normal.x (0)      (offset+j*2+1)*6+3 = bottom vertex normal.x
        #  (offset+j*2)*6+4 = top vertex normal.y (1)      (offset+j*2+1)*6+4 = bottom vertex normal.y (0)
        #  (offset+j*2)*6+5 = top vertex normal.y (0)      (offset+j*2+1)*6+5 = bottom vertex normal.z
        # jm is the poly_vs vertex index which precedes j (cyclically).
        jm = (len(poly_vs)//2-1) if j == 0 else (j-1)
        all_vs.extend([poly_vs[j*2], top, poly_vs[j*2+1], 0, 1, 0,
                       poly_vs[j*2], bottom, poly_vs[j*2+1],
                       poly_vs[j*2+1] - poly_vs[jm*2+1], 0, poly_vs[jm*2] - poly_vs[j*2]])
        # By using flat normals, we don't have to duplicate vertices.
        # By default, flat attributes take from the last vertex in each triangle.
        # As configured here, the leading bottom (j*2+1) has the required normal,
        # so we want to triangulate the face as such to hit j*2+1 last:
        #           (up normal)   jm*2  42--1  j*2   (up normal)
        #                               | \ |
        # (normal of prev face) jm*2+1  5--63  j*2+1 (normal of this face)
        all_trigs.extend([offset+j*2, offset+jm*2, offset+j*2+1,     # 1 2 3
                          offset+jm*2, offset+jm*2+1, offset+j*2+1])  # 4 5 6
        # since the top faces only use top vertices, which all have up normals, they are automatically fine.
        # NOTE: normals are not normalised here, but instead every frame in the vertex shader, which
        # sounds silly, but I want this here uncluttered, and the GPU isn't exactly struggling.
    t3.stop()

write(f'Triangulating buildings ({len(data.index)}/{len(data.index)})...')
print(f' done. ({t1.total(1)}+{t2.total(1)}+{t3.total(1)}={timer.lap(1)}s)')

print('Numpifying data...', end='')

vertices = np.array(all_vs, dtype='float32')
triangles = np.array(all_trigs, dtype='uint32')

print(f' done. ({timer.lap(2)}s)')
