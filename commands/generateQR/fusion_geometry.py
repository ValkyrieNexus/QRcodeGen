"""Fusion sketch drawing and extrusion helpers for QR code generation."""

import adsk.core
import adsk.fusion
import math


def mm_to_cm(mm_value):
    """Convert millimeters to centimeters (Fusion internal units)."""
    return mm_value / 10.0


def draw_square_module(sketch, col, row, total_rows, module_size_cm, spacing_cm=0.0):
    """Draw a single square module on the sketch.

    Args:
        sketch: adsk.fusion.Sketch
        col: Column index in QR matrix.
        row: Row index in QR matrix.
        total_rows: Total number of rows in the matrix.
        module_size_cm: Size of one module in cm.
        spacing_cm: Gap between modules in cm.
    """
    half_gap = spacing_cm / 2.0
    x0 = col * module_size_cm + half_gap
    y0 = (total_rows - 1 - row) * module_size_cm + half_gap
    x1 = (col + 1) * module_size_cm - half_gap
    y1 = (total_rows - row) * module_size_cm - half_gap

    lines = sketch.sketchCurves.sketchLines
    p1 = adsk.core.Point3D.create(x0, y0, 0)
    p2 = adsk.core.Point3D.create(x1, y1, 0)
    lines.addTwoPointRectangle(p1, p2)


def draw_circle_module(sketch, col, row, total_rows, module_size_cm, spacing_cm=0.0):
    """Draw a single circle module on the sketch.

    Args:
        sketch: adsk.fusion.Sketch
        col: Column index in QR matrix.
        row: Row index in QR matrix.
        total_rows: Total number of rows in the matrix.
        module_size_cm: Size of one module in cm.
        spacing_cm: Gap between modules in cm.
    """
    cx = (col + 0.5) * module_size_cm
    cy = (total_rows - 1 - row + 0.5) * module_size_cm
    radius = (module_size_cm - spacing_cm) / 2.0

    if radius <= 0:
        return

    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(cx, cy, 0)
    circles.addByCenterRadius(center, radius)


def draw_all_modules(sketch, module_positions, total_rows, module_size_cm,
                     spacing_cm=0.0, style='Square'):
    """Draw all QR modules on a sketch.

    Args:
        sketch: adsk.fusion.Sketch
        module_positions: list of (row, col) tuples for modules to draw.
        total_rows: Total rows in the QR matrix.
        module_size_cm: Module size in cm.
        spacing_cm: Spacing between modules in cm.
        style: 'Square' or 'Circle'.

    Returns:
        int: Number of modules drawn.
    """
    draw_fn = draw_circle_module if style == 'Circle' else draw_square_module
    count = 0
    for (row, col) in module_positions:
        draw_fn(sketch, col, row, total_rows, module_size_cm, spacing_cm)
        count += 1
    return count


def draw_frame(sketch, total_size_cm, frame_size_cm):
    """Draw a border frame around the QR code.

    Creates two concentric rectangles: outer frame and inner cutout.

    Args:
        sketch: adsk.fusion.Sketch
        total_size_cm: Total QR code size in cm (modules * module_size).
        frame_size_cm: Frame border width in cm.
    """
    lines = sketch.sketchCurves.sketchLines

    # Outer rectangle
    outer_p1 = adsk.core.Point3D.create(-frame_size_cm, -frame_size_cm, 0)
    outer_p2 = adsk.core.Point3D.create(
        total_size_cm + frame_size_cm,
        total_size_cm + frame_size_cm,
        0
    )
    lines.addTwoPointRectangle(outer_p1, outer_p2)

    # Inner rectangle (creates the frame profile between outer and inner)
    inner_p1 = adsk.core.Point3D.create(0, 0, 0)
    inner_p2 = adsk.core.Point3D.create(total_size_cm, total_size_cm, 0)
    lines.addTwoPointRectangle(inner_p1, inner_p2)


def extrude_all_profiles(component, sketch, depth_cm, body_prefix='QR_Module',
                         exclude_largest=False, progress_dialog=None):
    """Extrude all profiles in a sketch as separate bodies.

    Args:
        component: adsk.fusion.Component
        sketch: adsk.fusion.Sketch
        depth_cm: Extrusion depth in cm.
        body_prefix: Prefix for body names.
        exclude_largest: If True, skip the largest profile (background).
        progress_dialog: Optional adsk.core.ProgressDialog for cancellation.

    Returns:
        list: Created body objects.
    """
    extrudes = component.features.extrudeFeatures
    distance = adsk.core.ValueInput.createByReal(depth_cm)
    profiles = sketch.profiles
    bodies = []

    # Find largest profile area to optionally exclude
    largest_area = 0
    largest_idx = -1
    if exclude_largest and profiles.count > 1:
        for i in range(profiles.count):
            prof = profiles.item(i)
            area = prof.areaProperties().area
            if area > largest_area:
                largest_area = area
                largest_idx = i

    for i in range(profiles.count):
        if progress_dialog and progress_dialog.wasCancelled:
            break

        if exclude_largest and i == largest_idx:
            continue

        prof = profiles.item(i)
        try:
            ext_input = extrudes.createInput(
                prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )
            ext_input.setDistanceExtent(False, distance)
            feat = extrudes.add(ext_input)
            if feat and feat.bodies.count > 0:
                body = feat.bodies.item(0)
                body.name = f'{body_prefix}_{len(bodies) + 1:04d}'
                bodies.append(body)
        except Exception:
            # Skip profiles that fail to extrude (e.g., degenerate geometry)
            pass

        if progress_dialog:
            progress_dialog.progressValue += 1

    return bodies


def extrude_frame_profile(component, sketch, depth_cm):
    """Extrude the frame profile (the ring between outer and inner rectangles).

    The frame sketch has two concentric rectangles creating 2 profiles:
    the ring (frame) and the inner area. We want the ring.

    Args:
        component: adsk.fusion.Component
        sketch: adsk.fusion.Sketch
        depth_cm: Extrusion depth in cm.

    Returns:
        Body or None.
    """
    extrudes = component.features.extrudeFeatures
    distance = adsk.core.ValueInput.createByReal(depth_cm)
    profiles = sketch.profiles

    # The frame profile is the one that is NOT the inner rectangle
    # Find the profile with the larger area (the ring shape)
    # Actually in Fusion, the ring between two rectangles is its own profile
    # We need the profile that represents the frame border
    target_prof = None
    inner_area = float('inf')

    if profiles.count == 2:
        # Two profiles: inner rectangle and outer ring
        area0 = profiles.item(0).areaProperties().area
        area1 = profiles.item(1).areaProperties().area
        # The frame (ring) has a larger area than the inner square
        # Actually no - the ring area = outer_area - inner_area, which could be
        # smaller than inner_area. We want the ring, not the fill.
        # The inner rectangle profile is the one fully inside.
        # Pick the profile with the SMALLER area if frame is thin,
        # or we can just extrude both and name appropriately.
        # Safer: extrude the non-inner profile.
        # The inner profile has area = total_size^2
        # The frame profile has area = (total_size + 2*frame)^2 - total_size^2
        # For typical cases, the frame ring area < inner area
        # So pick the smaller area profile for the frame
        if area0 < area1:
            target_prof = profiles.item(0)
        else:
            target_prof = profiles.item(1)
    elif profiles.count == 1:
        target_prof = profiles.item(0)

    if target_prof:
        try:
            ext_input = extrudes.createInput(
                target_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )
            ext_input.setDistanceExtent(False, distance)
            feat = extrudes.add(ext_input)
            if feat and feat.bodies.count > 0:
                body = feat.bodies.item(0)
                body.name = 'QR_Frame'
                return body
        except Exception:
            pass
    return None


def create_component(root_comp, name):
    """Create a new component, or return root_comp if in a Part design.

    Part designs can only have one component. In that case we draw
    directly in the root component instead of creating a sub-component.

    Args:
        root_comp: Root component.
        name: Name for the new component.

    Returns:
        adsk.fusion.Component: The component to draw in.
    """
    try:
        occ = root_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = name
        return comp
    except Exception:
        # Part design -- can't add components, use root directly
        return root_comp
