IBL Toolkit
===========
TO BE UPDATED SOON - 4.2013


OLD DOC:

http://www.dalaifelinto.com/ftp/impa/ibl_toolkit_beta.zip
23.05.2012 - requires Blender svn (2.63a < rev.46953 < *your blender*)

** how to install it **
in the addon panel (in user preferences) click in "Install Addon" and select the zip file.
(no need to unzip it)

** calibration **

(1) go to movie clip editor and load your IBL or a LDR "proxy"
[example of extreme rotated map]
http://www.dalaifelinto.com/ftp/impa/tokyo-rotated.jpg
[for other maps go to http://smartibl.com/sibl/monthly.html or www.hdrlabs.com/sibl/archive.html]
[a LDR proxy (e.g. JPG) can be used instead of the HDR, see (6.1)]
[avoid using numbers in the image name, so the image is always present regardless of the current frame]

(2) in the movieclip mark 4 points counter-clockwise that makes a rectangle in the real world ON THE FLOOR
(mark point == Ctrl + LBM)
(2.1) After adding, select them all (shift+b, a, ...)

(3) in the movie editor left menu panel you will see IBL Calibration
(4) press "Calibrate IBL Orientation"
[this will calculate the orientation in order to the selected rectangle to be on the floor
also it projects the rectangle in the 3d view (see 8 to adjust that)]

(5) switch to Cycles engine or LuxRender
(6) press "Set IBL as Background"
[this creates the necessary nodes to setup the background with the calculated orientation]
(6.1) if you want to use a different map (e.g. a HDR one, while keep a LDR for editing) select the file in the box.

(7) eyeballing: if you want to tweak the rotation you can change the angles in the panel while
"Background Live Update" is marked
[this will update the cycles background in realtime]

(8) in the reference option you can adjust the camera height of your scene or the plane dimensions.
[this will change the plane object and the camera BUT will not change the other already added objects.


** Floor Reconstruction **

(1) Draw Polygon: it takes all the selected points and project them in the 3d world
making a polygon connecting them all
[the vertices are ordered by their creation order, not selection order]

(2) Draw Square: it takes 2 selected points and draw a square in 3d world using them as corners.

(3) Draw Circle: it takes 3 selected points and draw a circle in 3d world

(4) Draw Rectangle: it takes 3 selected points and draw a rectangle.
[* barely functional, complicated math, it may be removed from the final version *]


** World Reconstruction **

Cycles 'rendered' mode doesn't show the meshes in edit mode.
It's also too slow to wait for the background to clean everytime you move an object to match the environment.

(1) In the 3dView property panel open the 'Panorama Background' panel
(2) click in 'IBL in 3d View'
(2.1) in rendered mode you will see no difference
(2.2) in texture, solid an material modes you will see the ibl plate as a background
(2.3) in wireframe and bounding box modes you will see the ibl plate blended with the foreground

** Render **

There are extra operators to use that can help the rendering. They were done with Luxrender in mind, but some work with
Cycles as well.

(1) Panorama Camera : creates a camera that will render a panorama that matches the original panorama orientation.
    * remember to set the output dimensions (width x height) to match
    your panorama size (or at least keep within the aspect ratio 2:1

(2) Project UV : adds an UV layer to the selected object with the environment UV. If you use the original panorama
    as texture this will map the image in the object.
    * see this as a fancy camera mapping: e.g, http://www.dalaifelinto.com/?p=469
    * the more subdvided the mesh, the more it will match the 'curved' space of the panorama image

(3) Render Depth : renders the scene and store the depth information of the support geometry in the HDRI file.
    needed for the EnvPath integrator
    * (AR) Luxrender only *


important:
* this operator is a bit unstable. Save your file often when using it.
* if you want to stop the operator press ESC
* HDR images will not work, only LDR (e.g. JPG - see calibration(6.1))
* this only works well for perspective cameras. If you are using a panorama or orthographic
  cameras you should temporarily change it to perspective while editing the world.

** What comes next **
1) draw feedback (opengl drawing of line, axes, ... in the movie editor)
2) polishing

** credits **
Plugin Development: Dalai Felinto and Aldo Zang
Supervision: Luiz Velho

