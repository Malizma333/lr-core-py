# Compile-time booleans that enable features not represented by track files (and cause certain tests to fail)

# The linerider.com scarf uses trig operations that are difficult to replicate in other languages
# However, the flash version does not, making it much more testable
# Turn this on to get approximately the effect of the linerider.com scarf
LR_COM_SCARF = False

# Beta builds 6.3 and 6.7 have a bug where the gravity is off by a very small amount,
# but other than that they work identically to 6.2 physics
# (try loading phunner.track.json 21 seconds in)
GRAVITY_FIX = False

# LRA and OpenLR incorrectly add offsets to contact points before calculating bone lengths, causing
# issues with certain offset values from flash or linerider.com tracks
OFFSET_BEFORE_BONES = False
