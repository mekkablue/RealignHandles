# encoding: utf-8

###########################################################################################################
#
#
# Filter without dialog plug-in
#
# Read the docs:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Filter%20without%20Dialog
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs, GSSMOOTH, GSOFFCURVE
from GlyphsApp.plugins import FilterWithoutDialog
from AppKit import NSPoint, NSEvent, NSEventModifierFlagOption


def straightenBCPs(layer):

	def triplet(n1, n2, n3):
		return (*n1.position, *n2.position, *n3.position)

	def closestPointOnLine(P, A, B):
		# vector of line AB
		AB = NSPoint(B.x - A.x, B.y - A.y)
		# vector from point A to point P
		AP = NSPoint(P.x - A.x, P.y - A.y)
		# dot product of AB and AP
		dotProduct = AB.x * AP.x + AB.y * AP.y
		ABsquared = AB.x**2 + AB.y**2
		t = dotProduct / ABsquared
		x = A.x + t * AB.x
		y = A.y + t * AB.y
		return NSPoint(x, y)

	def ortho(n1, n2):
		xDiff = n1.x - n2.x
		yDiff = n1.y - n2.y
		# must not have the same coordinates,
		# and either vertical or horizontal:
		if xDiff != yDiff and xDiff * yDiff == 0.0:
			return True
		return False

	handleCount = 0
	for p in layer.paths:
		for n in p.nodes:
			if n.connection != GSSMOOTH:
				continue
			nn, pn = n.nextNode, n.prevNode
			if all((nn.type == GSOFFCURVE, pn.type == GSOFFCURVE)):
				# surrounding points are BCPs
				smoothen, center, opposite = None, None, None
				for handle in (nn, pn):
					if ortho(handle, n):
						center = n
						opposite = handle
						smoothen = nn if nn != handle else pn
						oldPos = triplet(smoothen, center, opposite)
						p.setSmooth_withCenterNode_oppositeNode_(smoothen, center, opposite)
						if oldPos != triplet(smoothen, center, opposite):
							handleCount += 1
						break
				if smoothen == center == opposite is None:
					oldPos = triplet(n, nn, pn)
					n.position = closestPointOnLine(n.position, nn, pn)
					if oldPos != triplet(n, nn, pn):
						handleCount += 1
			elif n.type != GSOFFCURVE and (nn.type, pn.type).count(GSOFFCURVE) == 1:
				# only one of the surrounding points is a BCP
				center = n
				if nn.type == GSOFFCURVE:
					smoothen = nn
					opposite = pn
				elif pn.type == GSOFFCURVE:
					smoothen = pn
					opposite = nn
				else:
					continue  # should never occur
				oldPos = triplet(smoothen, center, opposite)
				p.setSmooth_withCenterNode_oppositeNode_(smoothen, center, opposite)
				if oldPos != triplet(smoothen, center, opposite):
					handleCount += 1
	return handleCount


class RealignHandles(FilterWithoutDialog):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': 'Realign Handles',
			'de': 'Anfasser neu ausrichten',
			'fr': 'Realigner poignées',
			'es': 'Realinear manejadores',
		})


	@objc.python_method
	def filter(self, layer, inEditView, customParameters):
		shouldProcessAllMasters = False
		if inEditView:
			keysPressed = NSEvent.modifierFlags()
			shouldProcessAllMasters = keysPressed & NSEventModifierFlagOption == NSEventModifierFlagOption
		
		glyph = layer.parent
		if shouldProcessAllMasters:
			for everyLayer in glyph.layers:
				if everyLayer.isMasterLayer or everyLayer.isSpecialLayer:
					straightenBCPs(everyLayer)
		else:
			straightenBCPs(layer)


	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
