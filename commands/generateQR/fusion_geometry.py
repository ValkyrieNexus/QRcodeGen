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
                     spacing_cm=0.0, style='Square', offset_x=0, offset_y=0):
    """Draw all QR modules on a sketch with optional offset.

    Args:
        sketch: adsk.fusion.Sketch
        module_positions: list of (row, col) tuples for modules to draw.
        total_rows: Total rows in the QR matrix.
        module_size_cm: Module size in cm.
        spacing_cm: Spacing between modules in cm.
        style: 'Square' or 'Circle'.
        offset_x: X offset in cm for centering.
        offset_y: Y offset in cm for centering.

    Returns:
        int: Number of modules drawn.
    """
    lines = sketch.sketchCurves.sketchLines
    circles = sketch.sketchCurves.sketchCircles

    # Micro-gap prevents adjacent module rectangles from sharing edges,
    # which would cause Fusion to merge profiles unpredictably.
    # 0.001 cm = 0.01 mm -- invisible but prevents edge merging.
    micro_gap = 0.001
    half_gap = max(spacing_cm / 2.0, micro_gap)
    count = 0

    for (row, col) in module_positions:
        if style == 'Circle':
            cx = offset_x + (col + 0.5) * module_size_cm
            cy = offset_y + (total_rows - 1 - row + 0.5) * module_size_cm
            radius = (module_size_cm - spacing_cm) / 2.0 - micro_gap
            if radius > 0:
                circles.addByCenterRadius(adsk.core.Point3D.create(cx, cy, 0), radius)
        else:
            x0 = offset_x + col * module_size_cm + half_gap
            y0 = offset_y + (total_rows - 1 - row) * module_size_cm + half_gap
            x1 = offset_x + (col + 1) * module_size_cm - half_gap
            y1 = offset_y + (total_rows - row) * module_size_cm - half_gap
            p1 = adsk.core.Point3D.create(x0, y0, 0)
            p2 = adsk.core.Point3D.create(x1, y1, 0)
            lines.addTwoPointRectangle(p1, p2)
        count += 1

    return count


def draw_frame(sketch, total_size_cm, frame_size_cm, offset_x=0, offset_y=0):
    """Draw a border frame around the QR code.

    Creates two concentric rectangles: outer frame and inner cutout.

    Args:
        sketch: adsk.fusion.Sketch
        total_size_cm: Total QR code size in cm (modules * module_size).
        frame_size_cm: Frame border width in cm.
        offset_x: X offset in cm.
        offset_y: Y offset in cm.
    """
    lines = sketch.sketchCurves.sketchLines

    # Outer rectangle
    outer_p1 = adsk.core.Point3D.create(offset_x - frame_size_cm, offset_y - frame_size_cm, 0)
    outer_p2 = adsk.core.Point3D.create(
        offset_x + total_size_cm + frame_size_cm,
        offset_y + total_size_cm + frame_size_cm,
        0
    )
    lines.addTwoPointRectangle(outer_p1, outer_p2)

    # Inner rectangle (creates the frame profile between outer and inner)
    inner_p1 = adsk.core.Point3D.create(offset_x, offset_y, 0)
    inner_p2 = adsk.core.Point3D.create(offset_x + total_size_cm, offset_y + total_size_cm, 0)
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


def extrude_profiles_combined(component, sketch, depth_cm, body_name='QR_Modules',
                              exclude_largest=False):
    """Extrude all profiles and combine into a single body.

    Collects all valid profiles into an ObjectCollection, extrudes them
    in one operation, then uses CombineFeature to union all resulting
    bodies into one named body.

    Args:
        component: adsk.fusion.Component
        sketch: adsk.fusion.Sketch
        depth_cm: Extrusion depth in cm.
        body_name: Name for the final combined body.
        exclude_largest: If True, skip the largest profile (background).

    Returns:
        adsk.fusion.BRepBody or None: The single combined body.
    """
    profiles = sketch.profiles
    extrudes = component.features.extrudeFeatures
    distance = adsk.core.ValueInput.createByReal(depth_cm)

    # Find largest profile to exclude (background)
    largest_idx = -1
    if exclude_largest and profiles.count > 1:
        largest_area = 0
        for i in range(profiles.count):
            area = profiles.item(i).areaProperties().area
            if area > largest_area:
                largest_area = area
                largest_idx = i

    # Collect valid profiles into ObjectCollection
    prof_collection = adsk.core.ObjectCollection.create()
    for i in range(profiles.count):
        if i == largest_idx:
            continue
        prof_collection.add(profiles.item(i))

    if prof_collection.count == 0:
        return None

    # Single extrude operation for all profiles at once
    try:
        ext_input = extrudes.createInput(
            prof_collection,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext_input.setDistanceExtent(False, distance)
        feat = extrudes.add(ext_input)
    except Exception:
        # If batch extrude fails, fall back to individual extrusions
        app = adsk.core.Application.get()
        app.log(f'QRcodeGen: Batch extrude failed for {prof_collection.count} profiles, falling back to individual')
        bodies = []
        for i in range(prof_collection.count):
            try:
                single_input = extrudes.createInput(
                    prof_collection.item(i),
                    adsk.fusion.FeatureOperations.NewBodyFeatureOperation
                )
                single_input.setDistanceExtent(False, distance)
                f = extrudes.add(single_input)
                if f and f.bodies.count > 0:
                    bodies.append(f.bodies.item(0))
            except Exception:
                pass
        if not bodies:
            return None
        target = bodies[0]
        if len(bodies) > 1:
            tool_col = adsk.core.ObjectCollection.create()
            for b in bodies[1:]:
                tool_col.add(b)
            try:
                ci = component.features.combineFeatures.createInput(target, tool_col)
                ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
                ci.isKeepToolBodies = False
                component.features.combineFeatures.add(ci)
            except Exception:
                pass
        target.name = body_name
        return target

    if not feat or feat.bodies.count == 0:
        return None

    # If only one body resulted, just name it and return
    if feat.bodies.count == 1:
        feat.bodies.item(0).name = body_name
        return feat.bodies.item(0)

    # Combine all bodies into one using CombineFeature
    target_body = feat.bodies.item(0)
    tool_bodies = adsk.core.ObjectCollection.create()
    for i in range(1, feat.bodies.count):
        tool_bodies.add(feat.bodies.item(i))

    try:
        combine_input = component.features.combineFeatures.createInput(
            target_body, tool_bodies
        )
        combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        combine_input.isKeepToolBodies = False
        component.features.combineFeatures.add(combine_input)
    except Exception:
        # If combine fails (coincident faces), leave as separate bodies
        pass

    target_body.name = body_name
    return target_body


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


def measure_face_bounds(face):
    """Measure a planar face's width and height.

    Uses a temporary sketch on the face to get accurate dimensions
    in the face's local coordinate system.

    Returns:
        tuple: (width_cm, height_cm) or None if unmeasurable.
    """
    bbox = face.boundingBox
    if not bbox:
        return None

    # Use world bounding box -- take the two largest extents
    dx = abs(bbox.maxPoint.x - bbox.minPoint.x)
    dy = abs(bbox.maxPoint.y - bbox.minPoint.y)
    dz = abs(bbox.maxPoint.z - bbox.minPoint.z)
    dims = sorted([dx, dy, dz], reverse=True)
    return (dims[0], dims[1])


def cut_and_fill_on_face(component, target_face, target_body, module_positions,
                         total_rows, total_size_cm, seg_size_cm, spacing_cm,
                         depth_cm, style, frame_on, frame_size_cm,
                         icon_sketch_fn=None, auto_cut=True):
    """Generate QR code directly on an existing face with cut recess + fill.

    Auto-scales the QR code to fit within the face bounds. Cuts module-shaped
    recesses into the target body, then extrudes colored fill bodies.

    Args:
        component: Component that owns the target body.
        target_face: BRepFace to place QR on.
        target_body: BRepBody that owns the face.
        module_positions: List of (row, col) for dark modules.
        total_rows: Number of rows in QR matrix.
        total_size_cm: Total QR size in cm (before auto-scaling).
        seg_size_cm: Module size in cm (before auto-scaling).
        spacing_cm: Gap between modules in cm (before auto-scaling).
        depth_cm: Cut/fill depth in cm.
        style: 'Square' or 'Circle'.
        frame_on: Whether to add frame.
        frame_size_cm: Frame width in cm (before auto-scaling).
        icon_sketch_fn: Optional callable(sketch) to draw icon.

    Returns:
        dict with keys 'modules_body', 'frame_body', 'icon_body' (any may be None).
    """
    extrudes = component.features.extrudeFeatures
    result = {'modules_body': None, 'frame_body': None, 'icon_body': None}

    # ── Create a construction plane coincident with the face ──
    # Sketching directly on a BRepFace causes Fusion to auto-project face
    # boundary edges into the sketch, which corrupts QR module profiles.
    # Using a construction plane at zero offset avoids this entirely.
    planes = component.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(target_face, adsk.core.ValueInput.createByReal(0))
    ref_plane = planes.add(plane_input)

    # ── Measure face and compute centering ──
    # Use a single measurement sketch to find face center and dimensions
    measure_sketch = component.sketches.add(ref_plane)
    face_center = measure_sketch.modelToSketchSpace(target_face.centroid)

    # Project face edges to measure dimensions in sketch space
    face_w = 0
    face_h = 0
    try:
        outer_loop = target_face.loops.item(0)
        for i in range(outer_loop.edges.count):
            try:
                measure_sketch.project(outer_loop.edges.item(i))
            except Exception:
                pass
        if measure_sketch.profiles.count > 0:
            pbb = measure_sketch.profiles.item(0).boundingBox
            face_w = abs(pbb.maxPoint.x - pbb.minPoint.x)
            face_h = abs(pbb.maxPoint.y - pbb.minPoint.y)
    except Exception:
        pass
    measure_sketch.deleteMe()

    face_min = min(face_w, face_h) if face_w > 0 and face_h > 0 else 0

    # Auto-scale QR to fit within the face
    qr_with_frame = total_size_cm + (2 * frame_size_cm if frame_on else 0)
    if qr_with_frame > 0 and face_min > 0:
        available = face_min * 0.95
        if qr_with_frame > available:
            scale = available / qr_with_frame
            seg_size_cm = seg_size_cm * scale
            spacing_cm = spacing_cm * scale
            frame_size_cm = frame_size_cm * scale
            total_size_cm = total_rows * seg_size_cm

    # Center QR on the face center (sketch-space coordinates)
    offset_x = face_center.x - total_size_cm / 2.0
    offset_y = face_center.y - total_size_cm / 2.0

    # ── 1. Optionally cut a recess into the target body ──
    if auto_cut:
        cut_sketch = component.sketches.add(ref_plane)
        cut_sketch.name = 'QR_Recess_Cut'

        if frame_on:
            cp1 = adsk.core.Point3D.create(
                offset_x - frame_size_cm, offset_y - frame_size_cm, 0)
            cp2 = adsk.core.Point3D.create(
                offset_x + total_size_cm + frame_size_cm,
                offset_y + total_size_cm + frame_size_cm, 0)
        else:
            cp1 = adsk.core.Point3D.create(offset_x, offset_y, 0)
            cp2 = adsk.core.Point3D.create(
                offset_x + total_size_cm, offset_y + total_size_cm, 0)

        cut_sketch.sketchCurves.sketchLines.addTwoPointRectangle(cp1, cp2)
        cut_prof = cut_sketch.profiles.item(0)

        cut_input = extrudes.createInput(
            cut_prof, adsk.fusion.FeatureOperations.CutFeatureOperation
        )
        cut_dist = adsk.core.ValueInput.createByReal(depth_cm)
        cut_input.setDistanceExtent(False, cut_dist)
        cut_input.participantBodies = [target_body]
        extrudes.add(cut_input)

    # ── 2. Draw modules on construction plane ──
    mod_sketch = component.sketches.add(ref_plane)
    mod_sketch.name = 'QR_Modules_Sketch'
    draw_all_modules(mod_sketch, module_positions, total_rows,
                     seg_size_cm, spacing_cm, style, offset_x, offset_y)

    # Step A: Cut module shapes into the body (creates pockets)
    mod_profiles = adsk.core.ObjectCollection.create()
    for i in range(mod_sketch.profiles.count):
        mod_profiles.add(mod_sketch.profiles.item(i))

    if mod_profiles.count > 0:
        try:
            cut_mod = extrudes.createInput(
                mod_profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_mod.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth_cm))
            cut_mod.participantBodies = [target_body]
            extrudes.add(cut_mod)
        except Exception:
            pass

    # Step B: Fill pockets with new bodies (same sketch, same profiles)
    # Re-draw modules on a fresh sketch for the fill extrusion
    fill_sketch = component.sketches.add(ref_plane)
    fill_sketch.name = 'QR_Modules_Fill'
    draw_all_modules(fill_sketch, module_positions, total_rows,
                     seg_size_cm, spacing_cm, style, offset_x, offset_y)

    modules_body = extrude_profiles_combined(
        component, fill_sketch, depth_cm, 'QR_Modules', False
    )
    result['modules_body'] = modules_body

    # ── 3. Frame (if enabled) ──
    if frame_on:
        # Cut frame shape
        frame_cut_sketch = component.sketches.add(ref_plane)
        frame_cut_sketch.name = 'QR_Frame_Cut'
        draw_frame(frame_cut_sketch, total_size_cm, frame_size_cm, offset_x, offset_y)
        # Find the frame profile (smaller area of the two)
        if frame_cut_sketch.profiles.count >= 2:
            areas = []
            for i in range(frame_cut_sketch.profiles.count):
                areas.append((frame_cut_sketch.profiles.item(i).areaProperties().area, i))
            areas.sort()
            frame_prof = frame_cut_sketch.profiles.item(areas[0][1])
            try:
                fc_input = extrudes.createInput(
                    frame_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
                fc_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth_cm))
                fc_input.participantBodies = [target_body]
                extrudes.add(fc_input)
            except Exception:
                pass

        # Fill frame with new body
        frame_fill_sketch = component.sketches.add(ref_plane)
        frame_fill_sketch.name = 'QR_Frame_Fill'
        draw_frame(frame_fill_sketch, total_size_cm, frame_size_cm, offset_x, offset_y)
        frame_body = extrude_frame_profile(component, frame_fill_sketch, depth_cm)
        result['frame_body'] = frame_body

    # ── 4. Icon (if provided) ──
    if icon_sketch_fn:
        icon_sketch = component.sketches.add(ref_plane)
        icon_sketch.name = 'QR_Icon_Sketch'
        icon_sketch_fn(icon_sketch)
        icon_body = extrude_profiles_combined(
            component, icon_sketch, depth_cm, 'QR_Icon', True
        )
        result['icon_body'] = icon_body

    return result
