import bpy
from math import pi
from mathutils import Matrix
bl_info = {
    "name": "Radial Array Around Cursor",
    "author": "Brandon Bien",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Object Menu",
    "description": "Radial Array Around Cursor",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}




class BB_OT_RadialArray(bpy.types.Operator):
    """Create a Radial Array around the cursor"""
    bl_idname = 'object.radial_array'
    bl_label = 'Radial Array'
    bl_options = {'REGISTER', 'UNDO'}

    # Create the variables for the radial array
    radial_array_enum: bpy.props.EnumProperty(
        name='Axis',
        description='Radial Array Axis',
        items=[
            ('X','X','X Axis', 0),
            ('Y','Y','Y Axis', 1),
            ('Z','Z','Z Axis', 2),
        ]
    )
    radial_array_amount: bpy.props.IntProperty(
        name='Copies',
        description='Number of Copies',
        default=3,
        min=3, soft_max = 32,
        max = 256,
    )
    radial_array_selection: bpy.props.EnumProperty(
        name='Duplication Type',
        description='Radial Array Type',
        items=[
            ('Modifier','Modifier','Modifier', 0),
            ('Instance','Instance','Instance', 1),
        ]
    )
    radial_array_offset: bpy.props.BoolProperty(
        name='Offset Array',
        description='Rotate the array by half of its angle'
    )
    @classmethod
    def poll(cls,context):
        return context.area.type == 'VIEW_3D'
    def execute(self, context):
        # Class for proper rotation in eulers and correct location for locators
        class arrayVectors:
            def  __init__(self, obVector, cursorVector, axis, copies):
                self.location = []
                if axis == 'X':
                #X
                    self.location = [obVector[0], cursorVector[1], cursorVector[2]]
                elif axis == 'Y':
                #Y
                    self.location = [cursorVector[0], obVector[1], cursorVector[2]]
                else:
                #Z
                    self.location = [cursorVector[0], cursorVector[1], obVector[2]]
                self.rotation = []
                if axis == 'X':
                    self.rotation = [pi*2/copies, 0, 0]
                elif axis == 'Y':
                    self.rotation = [0, pi*2/copies, 0]
                else:
                    self.rotation = [0, 0, pi*2/copies]
                self.rotationOffset = []
                if axis == 'X':
                    self.rotationOffset = [pi*2/copies/2, 0, 0]
                elif axis == 'Y':
                    self.rotationOffset = [0, pi*2/copies/2, 0]
                else:
                    self.rotationOffset = [0, 0, pi*2/copies/2]
        
        def find_collection(context, item):
            collections = item.users_collection
            if len(collections) > 0:
                return collections[0]
            return context.scene.collection

        def parent_keep_offset(parent,child):
            child.parent = parent
            child.matrix_parent_inverse = parent.matrix_basis.inverted()

        # Set  the Variables
        data = bpy.data
        cursor = context.scene.cursor
        copyOb = context.object
        obVectors =  arrayVectors(copyOb.location, cursor.location, self.radial_array_enum, self.radial_array_amount)
        copyObCollection = find_collection(context, copyOb)



        def modifierArray():
            # create empties
            empties = [data.objects.new('Radial Rotator', None),
            data.objects.new('Radial Rotator Child', None),
            data.objects.new(copyOb.name + ' Radial Array', None),
            ]
            # link to current collection and set visibility
            for e in empties:
                copyObCollection.objects.link(e)
            for e in range(0,2):
                empties[e].hide_viewport = True
            # set location
            empties[0].location = obVectors.location
            empties[1].location = copyOb.location
            # setup array modifier
            array_modifier = copyOb.modifiers.new('Radial Array', 'ARRAY')
            array_modifier.use_relative_offset = False
            array_modifier.use_object_offset = True
            array_modifier.offset_object = empties[1]
            array_modifier.count = self.radial_array_amount
            # parent empties
            parent_keep_offset(empties[0], empties[1])
            parent_keep_offset(copyOb, empties[0])
            parent_keep_offset(empties[2], copyOb)
            # do transform
            empties[0].rotation_euler = obVectors.rotation
            if self.radial_array_offset:
                empties[2].rotation_euler = obVectors.rotationOffset
            copyOb['RadialArray'] = True
            
        def linkedArray():
            # create empty
            centerEmpty = data.objects.new(copyOb.name + ' Radial Array', None)
            centerEmpty.location = obVectors.location
            copyObCollection.objects.link(centerEmpty)
            # Set the rotation matrix by transforming to the locator then transforming back
            rot = (Matrix.Translation(cursor.location) @ Matrix.Rotation(pi*2/self.radial_array_amount, 4, self.radial_array_enum) @ Matrix.Translation(-cursor.location))
            
            # create variables for linked copies
            iteration = 1
            obDupes = []
            arrayOb = copyOb.copy()
            #create the link  copies
            while iteration < self.radial_array_amount:
                copyObCollection.objects.link(arrayOb)
                arrayOb.matrix_world = rot @ arrayOb.matrix_world
                iteration += 1
                obDupes.append(arrayOb)
                arrayOb = arrayOb.copy()
            obDupes.append(copyOb)
            # parent items in array and transform if needed
            for ob in obDupes:
                parent_keep_offset(centerEmpty, ob)
            if self.radial_array_offset:
                centerEmpty.rotation_euler = obVectors.rotationOffset

        # Run the correct function based on array type
        if self.radial_array_selection == 'Modifier':
            modifierArray()
        else:
            linkedArray()

        return {'FINISHED'}


def menu_draw(self, context):
    self.layout.operator("object.radial_array")

bpy.types.VIEW3D_MT_object.append(menu_draw)


blender_classes = [
    BB_OT_RadialArray,
]

def register():

    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)


def unregister():
    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)

