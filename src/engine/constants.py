# Default size of cells within the physics simulation grid
DEFAULT_CELL_SIZE = 14

# Scalar applied to gravity values
GRAVITY_SCALAR = 0.175

# Beta 2 version 6.7 has a bug where the gravity value is off by one bit
GRAVITY_SCALAR_V67 = 0.17500000000000002

# Number of physics iterations bones go through when processing stretches and collisions
ITERATIONS = 6

# Default height of line hitboxes
DEFAULT_LINE_HITBOX_HEIGHT = 10

# Max ratio of the length of the line extension to the length of its line
MAX_EXTENSION_RATIO = 0.25

# Scalar applied to acceleration line vectors
ACCELERATION_SCALAR = 0.1

# The linerider.com scarf uses trig operations, causing unusable tests
# (comparing different sin implementations)
# However, the flash version does not, making it much more testable
# Turn this on to get approximately the effect of the linerider.com scarf
# (with failing tests)
USE_COM_SCARF = False
