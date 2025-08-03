# The linerider.com scarf uses trig operations, causing unusable tests
# (comparing different sin implementations)
# However, the flash version does not, making it much more testable
# Turn this on to get approximately the effect of the linerider.com scarf
# (with failing tests)
LR_COM_SCARF = False

# Beta builds 6.3 and 6.7 have a bug where the gravity is off by the least significant bit,
# but other than that they work identically to 6.0 physics
GRAVITY_FIX = False

# LRA dismount does not work exactly the same as flash and linerider.com
LRA_LEGACY_FAKIE_CHECK = False

# LRA remount is implemented completely differently from linerider.com
LRA_REMOUNT = False
