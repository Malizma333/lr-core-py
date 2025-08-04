# Compile-time booleans that enable features not represented by track files (and cause certain tests to fail)

# The linerider.com scarf uses trig operations that are difficult to replicate in other languages
# However, the flash version does not, making it much more testable
# Turn this on to get approximately the effect of the linerider.com scarf
LR_COM_SCARF = False

# Beta builds 6.3 and 6.7 have a bug where the gravity is off by a very small amount,
# but other than that they work identically to 6.2 physics
# (try loading phunner.track.json 21 seconds in)
GRAVITY_FIX = False

# LRA dismount does not work exactly the same as flash and linerider.com
# - sled breaks for shoulder fakie (which it shouldn't, according to flash)
# - sled doesn't ever break if bosh is dismounted (which it should still do for tail fakies, according to current .com)
LRA_LEGACY_FAKIE_CHECK = False

# LRA remount is implemented completely differently from linerider.com
LRA_REMOUNT = False
