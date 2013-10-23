#!/bin/bash

hdiutil eject /Volumes/STK/
hdiutil convert stk_template.sparseimage -format UDBZ -o stk_template.dmg
hdiutil convert stk_template.dmg -format UDSP -o STK
hdiutil mount STK.sparseimage
cp -r STK.app /Volumes/STK/
hdiutil eject /Volumes/STK/
hdiutil convert STK.sparseimage -format UDBZ -o STK.dmg